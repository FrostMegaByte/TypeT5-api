# TypeT5-API: an API for the Type Annotation Predictions of TypeT5
This repository is a fork of [TypeT5](https://github.com/utopia-group/TypeT5). Please see their original README for installation instructions. This README defines how to use the API.

## Disclaimer

This API only returns type annotation predictions for function parameters and the return type, as those are the only predictions needed for the related [PyHintSearch](https://github.com/FrostMegaByte/py-hint-search) project. However, TypeT5 is also able to determine type annotations for variable assignments. If you want this included, you shoud remove the `continue` statements in the `src/typet5/function_decoding.py` file related to `PythonVariable`s and rewrite the `src/api/api_response.py` file to include variable predictions. This is, however, not taken into account currently.

## Docker Setup (Easy)

1. Install [Docker](https://www.docker.com/)
2. Pull this project.
3. `cd TypeT5-api`
4. Build the Dockerfile by running `docker build -t typet5 .`
5. Then, to use the API, run `docker run -p 5000:5000 -v "PATH_OF_PROJECT_PYTHON_FILES_DIRECTORY":/app/data/code typet5`.  
_(Note: `PATH_OF_PROJECT_PYTHON_FILES_DIRECTORY` should have forward slashes.)_
6. Visit `localhost:5000` in the browser to see if the API is active.
7. Make a GET request to `localhost:5000/api` to get all type annotation predictions for the files in the provided project.  
_(Note: Receiving a response can take an extremely long time as TypeT5 is not very fast. The results are cached, so further calls to the API should be much faster)_
8. For [PyHintSearch](https://github.com/FrostMegaByte/py-hint-search) to be able to use the API, keep the Docker container running.

**Example:**  
1. You want to have type predictions for a locally stored project, e.g. you pulled [requests](https://github.com/psf/requests) into `D:/Documents`.
2. The `PATH_OF_PROJECT_PYTHON_FILES_DIRECTORY` that needs to be provided in this case would be `D:/Documents/requests/src/requests` as that is the location storing the Python files to annotate.

## Local Setup (Harder)

1. Pull this project.
2. `cd TypeT5-api`
3. Remove all files in the `data/code` directory and place your project Python files in this directory for which you want type annotation predictions.
4. `cd src/api` and then run the app.py file to start the Flask server.
5. Visit `localhost:5000` in the browser to see if the API is active.
6. Make a GET request to `localhost:5000/api` to get all type annotation predictions for the files in the provided project.  
_(Note: Receiving a response can take an extremely long time as TypeT5 is not very fast. The results are cached, so further calls to the API should be much faster)_
7. For [PyHintSearch](https://github.com/FrostMegaByte/py-hint-search) to be able to use the API, you should keep the `app.py` file running constantly.

**Example:**  
1. You want to have type predictions for a locally stored project, e.g. you pulled [requests](https://github.com/psf/requests) into `D:/Documents`.
2. Copy the Python files from `D:/Documents/requests/src/requests` into the `data/code` directory and start the API.