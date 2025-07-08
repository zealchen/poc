# Force rebuild with new platform
FROM public.ecr.aws/lambda/python:3.12

# Install build tools needed for pandas
RUN microdnf install -y gcc-c++

# Copy requirements first to leverage Docker layer caching
COPY timecard_processor/requirements.txt ${LAMBDA_TASK_ROOT}/

# Install the function's dependencies.
# This layer will be cached and only re-run if requirements.txt changes.
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Now copy the function code.
# If only this file changes, the build will be much faster as the layer above is cached.
COPY timecard_processor/timecard_processor.py ${LAMBDA_TASK_ROOT}/

# Add prompt.py and common folder
COPY timecard_processor/prompt.py ${LAMBDA_TASK_ROOT}/
COPY common/ ${LAMBDA_TASK_ROOT}/common/

# Set the CMD to your handler
CMD [ "timecard_processor.handler" ]