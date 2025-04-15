import os
from typing import List, Union

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException

from llm_guard.extended.exception import InferenceError
from llm_guard.util import get_logger

load_dotenv()

LOGGER = get_logger()


class InferenceClient:
    def __init__(self, model: str):
        """
        Initialize InferenceClient

        Args:
            model: Model identifier to use for inference

        Raises:
            InferenceError: If INFERENCE_URL is not set in environment variables
        """
        self.model = model
        self.inference_url = os.getenv("INFERENCE_URL")

        if not self.inference_url:
            raise InferenceError("INFERENCE_URL environment variable is not set")

    def perform_inference(
        self, input: Union[str, List[str]], retries: int = 3, timeout: int = 60
    ) -> List[str]:
        """
        Perform inference using the specified model

        Args:
            input: Input text or list of texts
            retries: Number of retry attempts
            timeout: Request timeout in seconds

        Returns:
            List of inference results

        Raises:
            InferenceError: If inference fails after all retries
        """

        for attempt in range(retries):
            try:
                response = requests.post(
                    self.inference_url, json={"model": self.model, "input": input}, timeout=timeout
                )

                # Check for successful response
                response.raise_for_status()

                # Validate response format
                result = response.json()

                if isinstance(result, dict):
                    if "error" in result:
                        raise InferenceError(result["error"].get("message", "Unknown error"))
                    elif "data" in result:
                        return result["data"]
                    else:
                        raise InferenceError("Unexpected response format")

                else:
                    raise InferenceError("Unexpected response format")

            except RequestException as e:
                LOGGER.warning("Inference attempt %d failed: %s", attempt + 1, str(e))
                if attempt < retries - 1:
                    continue

            except (ValueError, KeyError) as e:
                raise InferenceError(f"Invalid response format: {str(e)}")

        raise InferenceError(f"Failed to perform inference after {retries} attempts.")
