from pathlib import Path
import logging


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


request_logger = logging.getLogger("http.request")


class RequestLoggingMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		response = self.get_response(request)

		full_url = request.build_absolute_uri()
		message = f"{request.method} {request.get_full_path()} -> {response.status_code}"

		if response.status_code >= 400:
			request_logger.warning(message, extra={"url": full_url})
		else:
			request_logger.info(message, extra={"url": full_url})

		return response

	def process_exception(self, request, exception):
		full_url = request.build_absolute_uri()
		request_logger.exception(
			f"{request.method} {request.get_full_path()} -> unhandled exception: {exception}",
			extra={"url": full_url},
		)


LOGGING = {
	"version": 1,
	"disable_existing_loggers": False,
	"formatters": {
		"request": {
			"format": "%(asctime)s | %(levelname)s | %(url)s | %(message)s",
			"datefmt": "%Y-%m-%d %H:%M:%S",
		},
	},
	"handlers": {
		"console": {
			"class": "logging.StreamHandler",
			"formatter": "request",
		},
		"request_file": {
			"class": "logging.FileHandler",
			"filename": LOG_DIR / "requests.log",
			"formatter": "request",
			"level": "INFO",
		},
		"error_file": {
			"class": "logging.FileHandler",
			"filename": LOG_DIR / "errors.log",
			"formatter": "request",
			"level": "WARNING",
		},
	},
	"loggers": {
		"http.request": {
			"handlers": ["console", "request_file", "error_file"],
			"level": "INFO",
			"propagate": False,
		},
	},
}