"""
Description Builder - Extracted from MagicLiteralHandler
=========================================================

Handles description and recommendation generation for violations.
Part of Phase 1.5 to further decompose god objects.
"""

from typing import Any, Dict


class DescriptionBuilder:
    """
    Builds descriptions and recommendations for violations.

    Extracted from MagicLiteralHandler to reduce class size.
    """

    def __init__(self):
        """Initialize with default detection messages."""
        self.detection_messages = {
            "magic_literal": "Magic literal '{value}' should be a named constant",
            "magic_literal_contextual": "Magic literal '{value}' in {context}",
            "magic_literal_safe": "Low-priority magic literal '{value}'",
        }

    def set_messages(self, messages: Dict[str, str]):
        """Set custom detection messages."""
        self.detection_messages.update(messages)

    def create_description(self, value: Any, context_info: Dict) -> str:
        """Create a contextual description for the magic literal violation."""
        if context_info.get("context_type"):
            return self.detection_messages["magic_literal_contextual"].format(
                value=value, context=context_info["context_type"]
            )
        elif context_info.get("detected_context"):
            return self.detection_messages["magic_literal_contextual"].format(
                value=value, context=context_info["detected_context"] + " context"
            )
        elif context_info.get("severity_modifier") == "lower":
            return self.detection_messages["magic_literal_safe"].format(value=value)
        else:
            return self.detection_messages["magic_literal"].format(value=value)

    def get_recommendation(self, value: Any, context_info: Dict) -> str:
        """Get context-appropriate recommendation for magic literal."""
        base_recommendation = "Replace with a well-named constant or configuration value"

        if context_info.get("context_type") == "network_port":
            return "Define as a named constant like 'DEFAULT_PORT' or use configuration"
        elif context_info.get("context_type") == "buffer_size":
            return "Define as a named constant like 'BUFFER_SIZE' or 'CHUNK_SIZE'"
        elif context_info.get("detected_context") == "time":
            return "Define as a named constant like 'TIMEOUT_SECONDS' or 'DEFAULT_DELAY'"
        elif context_info.get("likely_array_index"):
            return "Consider using meaningful names for array indices or constants for offsets"
        elif context_info.get("likely_loop_counter"):
            return "Consider using named constants for loop limits or range bounds"
        elif isinstance(value, str) and context_info.get("likely_structured"):
            return "Consider using constants for format strings, templates, or structured data"
        else:
            return base_recommendation

    def create_formal_description(self, value: Any, formal_context, severity_score: float) -> str:
        """Create enhanced description using formal grammar context."""
        context_parts = []

        if formal_context.is_constant:
            context_parts.append("constant assignment")
        elif formal_context.is_configuration:
            context_parts.append("configuration context")
        elif formal_context.in_conditional:
            context_parts.append("conditional statement")
        elif formal_context.in_assignment:
            context_parts.append("variable assignment")

        location_parts = []
        if formal_context.class_name:
            location_parts.append(f"class {formal_context.class_name}")
        if formal_context.function_name:
            location_parts.append(f"function {formal_context.function_name}")

        location_str = " in " + ", ".join(location_parts) if location_parts else ""
        context_str = " (" + ", ".join(context_parts) + ")" if context_parts else ""

        severity_desc = (
            "high-priority" if severity_score > 7.0 else "medium-priority" if severity_score > 4.0 else "low-priority"
        )

        return f"{severity_desc.title()} magic literal '{value}'{context_str}{location_str}"

    def get_formal_recommendation(self, formal_context) -> str:
        """Get enhanced recommendations using formal grammar context."""
        recommendations = []

        if formal_context.is_constant:
            recommendations.append("Consider better naming or documentation for this constant")
        elif formal_context.is_configuration:
            recommendations.append("Move to configuration file or environment variable")
        else:
            recommendations.append("Extract to a named constant")

        if formal_context.in_conditional:
            recommendations.append("Magic literals in conditionals are error-prone - use named constants")

        if formal_context.variable_name:
            recommendations.append(
                f"Consider improving variable name '{formal_context.variable_name}' to be more descriptive"
            )

        if isinstance(formal_context.literal_value, str):
            recommendations.append("Consider using enums or string constants for better maintainability")
        elif isinstance(formal_context.literal_value, (int, float)):
            if formal_context.literal_value > 1000:
                recommendations.append("Large numbers should always be named constants")
            else:
                recommendations.append("Use descriptive constant names even for small numbers")

        return "; ".join(recommendations)
