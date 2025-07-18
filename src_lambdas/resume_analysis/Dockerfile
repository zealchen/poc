# Force rebuild with new platform
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements first to leverage Docker layer caching
COPY resume_analysis/requirements.txt ${LAMBDA_TASK_ROOT}/

# Install the function's dependencies.
# This layer will be cached and only re-run if requirements.txt changes.
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Now copy the function code.
# If only this file changes, the build will be much faster as the layer above is cached.
COPY resume_analysis/*.py ${LAMBDA_TASK_ROOT}/
COPY common/ ${LAMBDA_TASK_ROOT}/common/

# Set the CMD to your handler
CMD [ "index.handler" ]