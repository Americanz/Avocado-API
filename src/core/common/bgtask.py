from starlette.background import BackgroundTasks

from .ctx import CTX_BG_TASKS


class BgTasks:
    """Unified background management"""

    @classmethod
    async def init_bg_tasks_obj(cls):
        """Instantiate the background task and set it to the context"""
        bg_tasks = BackgroundTasks()
        CTX_BG_TASKS.set(bg_tasks)

    @classmethod
    async def get_bg_tasks_obj(cls):
        """Get the background task instance from the context"""
        return CTX_BG_TASKS.get()

    @classmethod
    async def add_task(cls, func, *args, **kwargs):
        """Adding a background task"""
        bg_tasks = await cls.get_bg_tasks_obj()
        bg_tasks.add_task(func, *args, **kwargs)  # type: ignore

    @classmethod
    async def execute_tasks(cls):
        """Execute background tasks, usually after the request result is returned"""
        bg_tasks = await cls.get_bg_tasks_obj()
        if bg_tasks.tasks:  # type: ignore
            await bg_tasks()  # type: ignore
