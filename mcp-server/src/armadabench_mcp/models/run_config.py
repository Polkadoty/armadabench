"""
Run Configuration Models

Configuration models for benchmark runs, including model settings,
benchmark parameters, and execution options.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator
import uuid


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    LOCAL = "local"


class ModelConfig(BaseModel):
    """
    Configuration for an LLM model.

    Specifies which model to use and its parameters.
    """
    provider: ModelProvider
    model_id: str
    api_key: str | None = None  # If None, reads from environment

    # Model parameters
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0

    # System prompt customization
    system_prompt_additions: str = ""

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v


class BenchmarkType(str, Enum):
    """Types of benchmarks available."""
    RULES_KNOWLEDGE = "rules_knowledge"
    LIST_BUILDING = "list_building"
    SPATIAL_REASONING = "spatial_reasoning"
    TACTICAL_PLAY = "tactical_play"
    FULL_GAME = "full_game"


class GameFormat(str, Enum):
    """Star Wars Armada game formats."""
    STANDARD = "standard"
    LEGACY = "legacy"
    TASK_FORCE = "task_force"
    SECTOR_FLEET = "sector_fleet"


class BenchmarkConfig(BaseModel):
    """
    Configuration for a benchmark run.

    Specifies what benchmarks to run and their parameters.
    """
    benchmark_types: list[BenchmarkType] = Field(
        default_factory=lambda: [BenchmarkType.RULES_KNOWLEDGE]
    )

    # Game settings
    game_format: GameFormat = GameFormat.LEGACY
    point_limit: int = 400

    # Scenario selection
    scenario_ids: list[str] | None = None  # If None, run all scenarios
    scenario_tags: list[str] = Field(default_factory=list)

    # Evaluation settings
    num_trials: int = 1
    randomize_scenarios: bool = False

    # Difficulty settings
    provide_hints: bool = False
    allow_takeback: bool = False


class VassalConfig(BaseModel):
    """
    Configuration for Vassal integration.
    """
    vassal_path: Path | None = None  # Path to VASSAL install
    module_path: Path | None = None  # Path to .vmod file
    java_path: Path | None = None  # Path to Java executable

    # Display settings
    headless: bool = True
    screenshot_enabled: bool = True

    # Timing
    action_delay_ms: int = 100
    screenshot_delay_ms: int = 500


class LoggingConfig(BaseModel):
    """
    Configuration for logging and data capture.
    """
    output_dir: Path = Field(default_factory=lambda: Path("./runs"))
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # What to log
    log_model_inputs: bool = True
    log_model_outputs: bool = True
    log_tool_calls: bool = True
    log_game_states: bool = True
    log_vassal_commands: bool = True

    # Screenshots
    capture_screenshots: bool = True
    screenshot_on_state_change: bool = True

    # Data export
    export_to_json: bool = True
    export_to_csv: bool = False


class RunConfig(BaseModel):
    """
    Complete configuration for a benchmark run.

    This is the top-level configuration that specifies everything
    needed to execute a reproducible benchmark run.
    """
    # Run identification
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    run_name: str = ""
    description: str = ""

    # Player models
    player1_model: ModelConfig
    player2_model: ModelConfig | None = None  # None = use baseline AI

    # Benchmark configuration
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)

    # Integration configs
    vassal: VassalConfig = Field(default_factory=VassalConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Execution settings
    timeout_per_turn: int = 300  # seconds
    timeout_per_game: int = 7200  # seconds (2 hours)
    max_turns_per_game: int = 100

    # Container settings
    container_image: str | None = None
    container_memory_limit: str = "8g"
    container_cpu_limit: int = 2

    # Random seed for reproducibility
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunConfig":
        """Create from dictionary."""
        return cls.model_validate(data)

    @classmethod
    def from_yaml(cls, path: Path) -> "RunConfig":
        """Load configuration from YAML file."""
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        import yaml
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


class RunResult(BaseModel):
    """
    Results from a benchmark run.
    """
    run_id: str
    run_name: str
    config: RunConfig

    # Timing
    start_time: str
    end_time: str
    duration_seconds: float

    # Results by benchmark type
    results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    # Aggregated metrics
    metrics: dict[str, float] = Field(default_factory=dict)

    # Errors and warnings
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Success status
    completed: bool = False
    success: bool = False
