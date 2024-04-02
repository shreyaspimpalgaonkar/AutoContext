# Hackathon Project Setup and Deployment

## Local Environment Setup

1. Ensure you have Python>=3.9 installed. If not, you can download it from [here](https://www.python.org/downloads/).

1. Clone the repository to your local machine.

1. Navigate to the project directory and install the project dependencies with pip:

```sh
pip install -r requirements.txt
```

5. Create a `.env` file in the project root directory and add the following environment variables:

```sh
SECRET_KEY=your_secret_key
```

## Running the Project
uvicorn main:web_app --reload

## Deployment
We use modal for deployment which should have been installed while installing the requirements.txt file.
Setup your modal account and token following the [docs](https://modal.com/docs/guide)

Serve the server for an ephemeral deployment using the following command:
```sh
modal serve main
```
Deploy the server for a permanent deployment using the following command:
```sh
modal deploy main
```