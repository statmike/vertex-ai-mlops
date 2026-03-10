"""Fine-tune DistilBERT on synthetic transaction data, upload to GCS."""

import argparse
import os
import subprocess
import tempfile

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, DistilBertModel


CATEGORIES = ["INCOME_WAGE", "INCOME_GIG", "EXPENSE"]

TRAINING_DATA = [
    ("Direct deposit payroll ACME Corp", 0),
    ("Salary payment biweekly", 0),
    ("Paycheck from employer", 0),
    ("Wages weekly deposit", 0),
    ("Employer compensation transfer", 0),
    ("Monthly salary credit", 0),
    ("Biweekly payroll deposit", 0),
    ("Annual bonus payment", 0),
    ("Overtime pay deposit", 0),
    ("Commission payment received", 0),
    ("Uber driver earnings payout", 1),
    ("Lyft ride payment", 1),
    ("Freelance web development payment", 1),
    ("DoorDash delivery earnings", 1),
    ("Fiverr gig completion payment", 1),
    ("Etsy shop sale proceeds", 1),
    ("TaskRabbit job payment", 1),
    ("Instacart shopper earnings", 1),
    ("YouTube ad revenue payout", 1),
    ("Upwork freelance contract payment", 1),
    ("Walmart grocery purchase", 2),
    ("Amazon order payment", 2),
    ("Netflix monthly subscription", 2),
    ("Gas station fuel purchase", 2),
    ("Restaurant dinner charge", 2),
    ("Utility bill payment electric", 2),
    ("Rent payment monthly", 2),
    ("Insurance premium auto", 2),
    ("Phone bill wireless carrier", 2),
    ("Coffee shop morning purchase", 2),
]


class TransactionDataset(Dataset):
    def __init__(self, data, tokenizer, max_length=128):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        text, label = self.data[idx]
        encoding = self.tokenizer(
            text, padding="max_length", truncation=True,
            max_length=self.max_length, return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long),
        }


def train(output_path: str, epochs: int = 20, lr: float = 2e-5):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    bert = DistilBertModel.from_pretrained("distilbert-base-uncased")
    hidden_size = bert.config.hidden_size
    classifier = nn.Linear(hidden_size, len(CATEGORIES))

    bert.to(device)
    classifier.to(device)

    # Repeat training data for more training signal
    augmented_data = TRAINING_DATA * 10
    dataset = TransactionDataset(augmented_data, tokenizer)
    loader = DataLoader(dataset, batch_size=8, shuffle=True)

    optimizer = torch.optim.AdamW(
        list(bert.parameters()) + list(classifier.parameters()), lr=lr
    )
    loss_fn = nn.CrossEntropyLoss()

    bert.train()
    classifier.train()

    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        total = 0
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            outputs = bert(input_ids=input_ids, attention_mask=attention_mask)
            cls_output = outputs.last_hidden_state[:, 0, :]
            logits = classifier(cls_output)
            loss = loss_fn(logits, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            preds = torch.argmax(logits, dim=-1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        acc = correct / total
        print(f"  Epoch {epoch+1}/{epochs} — loss={total_loss/len(loader):.4f} acc={acc:.3f}")

    # Save model
    with tempfile.TemporaryDirectory() as tmpdir:
        bert.save_pretrained(tmpdir)
        tokenizer.save_pretrained(tmpdir)
        torch.save(classifier.state_dict(), os.path.join(tmpdir, "classifier_head.pt"))

        print(f"Uploading model to {output_path}")
        subprocess.run(
            ["gsutil", "-m", "cp", "-r", f"{tmpdir}/*", output_path.rstrip("/") + "/"],
            check=True,
        )

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_path", required=True, help="GCS path for model artifacts")
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()
    train(args.output_path, args.epochs)
