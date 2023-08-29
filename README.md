# Web QA model specialized for single-hop accuracy

## Overview
The rapid evolution of artificial intelligence (AI) technology has unlocked new opportunities across various disciplines. However, despite many strides forward, current AI systems present a significant challenge: generating accurate search results from web-based data.

This challenge can be divided into two primary aspects: enhancing single-hop performance, which involves analyzing a single document or webpage to answer a given question, and improving multi-hop performance, where the AI model must navigate through multiple documents or webpages to answer a question, determining which information source to explore next. Presently, advanced models like GPT-4 have demonstrated impressive single-hop performance, surpassing smaller models even when fine-tuned for specific tasks. However, when it comes to tasks requiring reasoning abilities, even GPT-4 exhibits inconsistencies and inaccuracies. This issue stems from the limitations imposed by the structures of current large language models. While transformer-based models strive to maximize the probability of finding an answer, they lack true reasoning capabilities.

Therefore, I come up with a question answering (QA) model with enhanced one-hop precision and data retrieval and interpretation from the web.

## Experiment
Several factors hindered the ability to conduct large-scale experiments for this research. The following reasons contributed to the constraints:

One significant limitation was the cost associated with utilizing GPT-4 for experimentation purposes. Given the substantial computational resources required by this model, the expenses incurred proved to be prohibitive for conducting extensive experiments at a larger scale.

The program's current runtime performance presented another constraint. While striving to improve accuracy, certain trade-offs were made to optimize runtime efficiency. As a result, the program is currently slower than desired, which further constrained the scale of experiments that could be conducted within the available timeframe.

Another challenge encountered was the absence of a suitable dataset for evaluating hard one-hop questions that require advanced reasoning abilities. The existing datasets predominantly encompass simpler questions, lacking the necessary complexity and reasoning demands. As this research was conducted during a limited summer period, it was not feasible to create a comprehensive dataset that would adequately address the research problem.

Despite the limitations, GPT-4 was selected as the model for this research. The general nature of the research problem made it exceedingly challenging for other models, including those with fine-tuning capabilities, to surpass the performance of GPT-4.

As an illustration of the program's capabilities, an experiment was conducted using the question, "List all the academic departments at UIUC." By analyzing a single webpage from the link provided (https://directory.illinois.edu/departmentsUnits), the program generated a response that significantly outperformed existing alternatives such as Bing Chat, Bard, and other web-accessible chatbots, models, or agents. The program's output demonstrated superior accuracy and efficacy in retrieving the desired information from the web.

You can see the result at [sample_answer.txt](sample_answer.txt)

## Research Report
For more information, go to [my research report](research_report.pdf)

## Setup
1. Install Python 3.10

2. Install all the dependencies
```console
pip install -r requirements.txt
```
3. Run the program, this will start a chatbot, and currently it takes about 10-15 min to read a webpage and generate a response.
### Run on Windows
1. cd to the project folder
2. run the following command
```console
.\run.bat
```

### Run on MacOS or Linux
1. cd to the project folder
2. run the following command
```console
./run.sh
```

If that doesn't work, just do
```console
python3 main.py
```
or
```console
python main.py
```
