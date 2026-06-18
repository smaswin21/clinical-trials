from typing import Protocol

from config.state import CandidateTrial


class TrialSearchClient(Protocol):
	"""Protocol for components that retrieve candidate trials."""

	def search(
		self,
		diseases: list[str],
		medications: list[str],
		page_size: int,
	) -> list[CandidateTrial]: ...
