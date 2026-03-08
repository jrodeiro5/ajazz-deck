"""Configuration models for AJAZZ AKP153 button configuration."""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ButtonConfig(BaseModel):
    """Configuration for a single button."""

    model_config = ConfigDict(extra="allow")

    label: str | None = Field(None, description="Display label for the button")
    command: str | None = Field(None, description="Shell command to execute")
    script: str | None = Field(None, description="Script or multiline command")
    type: str | None = Field(
        None, description="Execution type: shell, clipboard, script"
    )
    image: str | None = Field(
        None, description="Optional path to icon file (96×96 PNG)"
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_command_from_script(cls, values):
        """If only script is provided, copy it to command for lookup convenience."""
        if isinstance(values, dict):
            command = values.get("command")
            script = values.get("script")
            if command is None and script is not None:
                values["command"] = script
        return values


class AjazzConfig(BaseModel):
    """Complete AJAZZ AKP153 configuration."""

    buttons: dict[int, ButtonConfig] = Field(
        default_factory=dict,
        description="Button configurations indexed by button ID (1-15)",
    )

    @field_validator("buttons")
    @classmethod
    def validate_button_ids(cls, v):
        """Validate button IDs are within valid range."""
        for button_id in v.keys():
            if not 1 <= button_id <= 15:
                raise ValueError(f"Button ID {button_id} must be between 1 and 15")
        return v

    @field_validator("buttons")
    @classmethod
    def validate_button_labels(cls, v):
        """Validate non-None button labels are unique."""
        labels = [config.label for config in v.values() if config.label is not None]
        if len(labels) != len(set(labels)):
            raise ValueError("Button labels must be unique")
        return v
