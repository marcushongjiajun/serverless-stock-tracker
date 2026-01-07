# 1. Use the official AWS Lambda base image for Python 3.11
FROM public.ecr.aws/lambda/python:3.11

# 2. Copy the requirements file into the container and install the dependencies.
# Note: Target the specific task root directory for Lambda
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# 3. Copy the Python script into the task root
COPY src/ ${LAMBDA_TASK_ROOT}/

# 4. Set the CMD to the name of the file and the function handler.
CMD [ "app.lambda_handler" ]