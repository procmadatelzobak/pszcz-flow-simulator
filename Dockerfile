FROM python:3.12-slim AS build
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

FROM python:3.12-slim
WORKDIR /app
COPY --from=build /usr/local /usr/local
EXPOSE 7777
CMD ["pszcz-server", "--host", "0.0.0.0"]
