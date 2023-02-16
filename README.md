# TypeT5: Seq2seq Type Inference using Static Analysis

This repo contains the source code for the paper [TypeT5: Seq2seq Type Inference using Static Analysis](https://openreview.net/forum?id=4TyNEhI2GdN&noteId=EX_-kP9xah).

## Installation

This project uses [pipenv](https://pipenv.pypa.io/en/latest/) to manage the package dependencies. Pipenv tracks the exact package versions and manages the (project-specific) virtual environment for you. To install all dependencies, make sure you have pipenv installed, then, at the project root, run:
```bash
pipenv sync
```

To add new dependences into the virtual environment, you can manually install them via `pipenv install ..` (using `pipenv`) or `pipenv run pip install ..` (using `pip` from within the virtual environment). If your pytorch installation is not working properly, you might need to install it via `pip` rather than `pipenv`. If you are not using pipenv, make sure to add the environment variables in `.env` to your environment when you run the programs.

You can run all unit tests by running `pipenv run pytest` at the project root.

## Running Trained Model
- TODO to download the pre-trained model weights.

## Dataset

- [scripts/collect_dataset.ipynb](scripts/collect_dataset.ipynb) downloads the creates the BetterTypes4Py dataset used in our paper.

- [scripts/analyze_dataset.ipynb](scripts/analyze_dataset.ipynb) computes basic statistics about our dataset.

## Training a New Model

- Run [scripts/train_model.py](scripts/train_model.py) to train a new TypeT5 model. Training takes about 11 hours on a single Quadro RTX 8000 GPU with 48GB memory.


## Development
Please see [DevGuide.md](DevGuide.md).
