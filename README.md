# Hackathon Project Setup and Deployment

## Environment Setup

1. Ensure you have Python 3.9 installed. If not, you can download it from [here](https://www.python.org/downloads/).

2. Install Poetry, which is used for dependency management in this project. You can install it by following the instructions [here](https://python-poetry.org/docs/#installation).

3. Clone the repository to your local machine.

4. Navigate to the project directory and install the project dependencies with Poetry:

```sh
poetry install
```

5. Create a `.env` file in the project root directory and add the following environment variables:

```sh
SECRET_KEY=your_secret_key
```

## Running the Project
uvicorn main:app --reload