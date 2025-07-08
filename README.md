# Timecard Processor

This project is an AWS CDK application that deploys a Timecard Processor service. The service uses a Lambda function to analyze uploaded timecard images, extract data from them using Amazon Bedrock, and store the results in a DynamoDB table. It provides a simple web interface built with Gradio for users to upload images and view the extracted data.

## Project Structure

- `app.py`: The entry point for the AWS CDK application.
- `demo/timecard_stack.py`: Defines the AWS CDK stack, including the DynamoDB table, Lambda function, and API Gateway.
- `src_lambdas/timecard_processor/`: Contains the source code for the timecard processor Lambda function.
  - `timecard_processor.py`: The main application logic, including the Gradio UI, FastAPI server, and Bedrock integration.
  - `Dockerfile`: The Dockerfile for building the Lambda function.
- `requirements.txt`: The Python dependencies for the project.
- `tests/`: Contains unit tests for the project.

## How it Works

1.  A user uploads a timecard image through the Gradio web interface.
2.  The image is sent to a Lambda function.
3.  The Lambda function sends the image to Amazon Bedrock with a prompt to extract the timecard data.
4.  The Lambda function parses the JSON response from Bedrock and stores the extracted data in a DynamoDB table.
5.  The user can view the extracted data in the Gradio interface.

## Setup and Deployment

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure AWS credentials:**

    Make sure your AWS credentials are configured correctly.

3.  **Deploy the CDK stack:**

    ```bash
    cdk deploy
    ```

4.  **Access the application:**

    After the deployment is complete, the CDK output will provide a URL for the API Gateway. You can access the Gradio web interface by opening this URL in your browser.

## Running Locally

To run the Gradio application on your local machine for development and testing, you can execute the `timecard_processor.py` script as a module. This is useful for iterating on the UI and application logic without needing to deploy to AWS.

1.  **Set up your environment:**

    Ensure you have the necessary dependencies installed:

    ```bash
    pip install -r src_lambdas/timecard_processor/requirements.txt
    ```

    You will also need to have your AWS credentials configured locally so the application can interact with Amazon Bedrock and DynamoDB.

2.  **Run the application:**

    Execute the following command from the root of the project directory:

    ```bash
    python -m src_lambdas.timecard_processor.timecard_processor
    ```

3.  **Access the application:**

    The application will be available at `http://127.0.0.1:7860` by default. Open this URL in your browser to interact with the Gradio interface.