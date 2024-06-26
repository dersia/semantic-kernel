# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.exceptions import KernelServiceNotFoundError

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import AI_SERVICE_CLIENT_TYPE, Kernel


class AIServiceSelector:
    """Default service selector, can be subclassed and overridden.

    To use a custom service selector, subclass this class and override the select_ai_service method.
    Make sure that the function signature stays the same.
    """

    def select_ai_service(
        self,
        kernel: "Kernel",
        function: "KernelFunction",
        arguments: "KernelArguments",
        type_: type["AI_SERVICE_CLIENT_TYPE"] | None = None,
    ) -> tuple["AI_SERVICE_CLIENT_TYPE", "PromptExecutionSettings"]:
        """Select an AI Service on a first come, first served basis,
        starting with execution settings in the arguments,
        followed by the execution settings from the function.
        If the same service_id is in both, the one in the arguments will be used.
        """
        if type_ is None:
            from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
            from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase

            type_ = (TextCompletionClientBase, ChatCompletionClientBase)

        execution_settings_dict = arguments.execution_settings or {}
        if func_exec_settings := getattr(function, "prompt_execution_settings", None):
            for id, settings in func_exec_settings.items():
                if id not in execution_settings_dict:
                    execution_settings_dict[id] = settings
        if not execution_settings_dict:
            from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

            execution_settings_dict = {"default": PromptExecutionSettings()}
        for service_id, settings in execution_settings_dict.items():
            try:
                service = kernel.get_service(service_id, type=type_)
            except KernelServiceNotFoundError:
                continue
            if service:
                service_settings = service.get_prompt_execution_settings_from_settings(settings)
                return service, service_settings
        raise KernelServiceNotFoundError("No service found.")
