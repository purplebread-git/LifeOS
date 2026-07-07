from abc import ABC, abstractmethod


class PluginManager(ABC):
    """Владеет жизненным циклом плагинов: регистрация + startup/shutdown.

    В отличие от PluginRegistry (чистое хранилище), PluginManager — это
    единственное место, где есть async-поведение, связанное с плагинами.
    """

    @abstractmethod
    async def start(self) -> None:
        """Зарегистрировать все плагины в registry и запустить их (on_startup)."""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Остановить все плагины (on_shutdown) в обратном порядке запуска."""
        raise NotImplementedError