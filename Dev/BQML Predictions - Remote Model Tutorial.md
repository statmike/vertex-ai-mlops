![ga4](https://www.google-analytics.com/collect?v=2&tid=G-6VDTYWLKX6&cid=1&en=page_view&sid=1&dl=statmike%2Fvertex-ai-mlops%2FDev&dt=BQML+Predictions+-+Remote+Model+Tutorial.md)

# BQML Remote Model Tutorial

- https://www.tensorflow.org/text/tutorials/classify_text_with_bert
- large BERT model: bert_en_cased_L-12_H-768_A-12
- (Modified it last layer activation function to sigmoid so that it can generate scores between 0-1)
- deploy it with n1-standard-4 CPU (autoscaling 1-10)
- It took around 40min to run on 10K dataset with batch size 64
- Try T4 GPU to train and server
