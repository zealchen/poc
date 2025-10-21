FROM public.ecr.aws/lambda/python:3.12
COPY ai_assessment_v2/requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt
COPY ai_assessment_v2/*.py ${LAMBDA_TASK_ROOT}
COPY common/ ${LAMBDA_TASK_ROOT}/common/
CMD [ "step_handler.handler" ]
