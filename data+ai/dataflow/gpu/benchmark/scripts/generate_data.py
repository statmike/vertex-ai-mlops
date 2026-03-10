"""Generate 100k synthetic transaction descriptions for benchmarking."""

import argparse
import os
import random

WAGE_TEMPLATES = [
    "Direct deposit payroll {company}",
    "Salary payment from {company}",
    "Biweekly wages {company}",
    "Paycheck deposit {company}",
    "Monthly salary {company}",
    "Compensation transfer {company}",
    "Employer payment {company}",
    "Weekly wages {company}",
    "Overtime pay {company}",
    "Bonus payment {company}",
]

GIG_TEMPLATES = [
    "{platform} driver earnings payout",
    "{platform} delivery payment",
    "Freelance {skill} payment received",
    "{platform} gig completion",
    "{platform} earnings deposit",
    "{platform} contractor payout",
    "Independent work {platform} payment",
    "{platform} service payment",
    "Gig economy {platform} earnings",
    "{platform} freelance deposit",
]

EXPENSE_TEMPLATES = [
    "{merchant} purchase {item}",
    "{merchant} payment",
    "{service} monthly subscription",
    "{merchant} order #{order_id}",
    "{service} bill payment",
    "{merchant} charge",
    "Payment to {merchant}",
    "{service} renewal",
    "{merchant} transaction",
    "{merchant} {item} purchase",
]

COMPANIES = [
    "ACME Corp", "TechStart Inc", "GlobalFin LLC", "MegaCorp", "DataSys",
    "CloudNet", "ByteWorks", "InfoTech", "NetGroup", "SysCo",
]

PLATFORMS = [
    "Uber", "Lyft", "DoorDash", "Instacart", "Fiverr",
    "Upwork", "TaskRabbit", "Postmates", "Grubhub", "Etsy",
]

SKILLS = [
    "web development", "graphic design", "writing", "data entry",
    "consulting", "photography", "video editing", "translation",
]

MERCHANTS = [
    "Walmart", "Amazon", "Target", "Costco", "Kroger",
    "Home Depot", "Best Buy", "Walgreens", "CVS", "Starbucks",
]

SERVICES = [
    "Netflix", "Spotify", "Electric", "Water", "Internet",
    "Phone", "Insurance", "Gym", "Cloud Storage", "Streaming",
]

ITEMS = [
    "groceries", "electronics", "clothing", "fuel", "household",
    "office supplies", "food", "beverages", "tools", "furniture",
]


def generate_transaction():
    category = random.choice(["wage", "gig", "expense"])

    if category == "wage":
        template = random.choice(WAGE_TEMPLATES)
        text = template.format(company=random.choice(COMPANIES))
    elif category == "gig":
        template = random.choice(GIG_TEMPLATES)
        text = template.format(
            platform=random.choice(PLATFORMS),
            skill=random.choice(SKILLS),
        )
    else:
        template = random.choice(EXPENSE_TEMPLATES)
        text = template.format(
            merchant=random.choice(MERCHANTS),
            service=random.choice(SERVICES),
            item=random.choice(ITEMS),
            order_id=random.randint(100000, 999999),
        )

    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100000, help="Number of transactions")
    parser.add_argument("--output", default="data/test_transactions.txt", help="Output file path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    with open(args.output, "w") as f:
        for _ in range(args.count):
            f.write(generate_transaction() + "\n")

    print(f"Generated {args.count} transactions -> {args.output}")


if __name__ == "__main__":
    main()
