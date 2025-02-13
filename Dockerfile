FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables
# ENV TZ=${TZ:-UTC} \
#     WEEKDAY_START=${WEEKDAY_START:-"18:00"} \
#     WEEKDAY_STOP=${WEEKDAY_STOP:-"00:00"} \
#     WEEKEND_START=${WEEKEND_START:-"10:00"} \
#     WEEKEND_STOP=${WEEKEND_STOP:-"00:00"}

# Run the script
CMD ["python", "scheduler.py"]
