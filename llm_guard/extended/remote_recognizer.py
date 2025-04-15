"""
Implementation for BudRemoteRecognizer.

Remote recognizers call external API
to get additional PII identification capabilities.
These results are added to all the other results
gathered by the different recognizers.

The actual call logic (e.g., HTTP or gRPC)
should be implemented within this class.
In this example, we use the `requests` package to perform a POST request.
Flow:
1. During `load`, call `supported_entities`
to get a list of what this service can detect
2. Translate the response coming from the `supported_entities` endpoint
3. During `analyze`, perform a POST request to the PII detector endpoint
4. Translate the response coming from the
PII detector endpoint into a List[RecognizerResult]
5. Return results
"""

import logging
from typing import List

from presidio_analyzer import RecognizerResult, RemoteRecognizer
from presidio_analyzer.nlp_engine import NlpArtifacts

from llm_guard.extended.util import InferenceClient
from llm_guard.model import Model

logger = logging.getLogger("presidio-analyzer")


class BudRemoteRecognizer(RemoteRecognizer):
    """
    A remote recognizer that calls an external API to get PII detection results.
    """

    def __init__(
        self,
        model: Model,
        supported_entities: list[str] | None = None,
        supported_language: str = "en",
    ):
        self._model = model
        self.supported_entities = supported_entities
        super().__init__(
            supported_entities=supported_entities,
            name=f"Remote recognizer {model.path}",
            supported_language=supported_language,
            version="1.0",
        )

    def load(self) -> None:
        """Call the get_supported_entities API of the external service.

        NOTE: Not needed for BudRemoteRecognizer.
        """

        pass

    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts
    ) -> List[RecognizerResult]:
        """Call an external service for PII detection."""

        response = InferenceClient(self._model.path).perform_inference(text)

        results = self._recognizer_results_from_response(response)

        return results

    def get_supported_entities(self) -> List[str]:
        """Return the list of supported entities."""

        return self.supported_entities

    def _recognizer_results_from_response(
        self,
        response: list,
    ) -> List[RecognizerResult]:
        """Translate the service's response to a list of RecognizerResult."""

        results = self._parse_recognizer_results(response)

        recognizer_results = [RecognizerResult(**result) for result in results]

        return recognizer_results

    @staticmethod
    def _parse_recognizer_results(response: list) -> List[RecognizerResult]:
        """Translate the service's response to a list of RecognizerResult."""

        results = []
        if len(response) == 0:
            return results

        for result in response[0]:
            result["entity_type"] = result["entity"]
            result.pop("entity")
            result.pop("index")
            result.pop("word")

            results.append(result)

        return results
