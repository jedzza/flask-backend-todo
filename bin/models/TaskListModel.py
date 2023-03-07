from pydantic import BaseModel

from bin.models.TaskModel import TaskModel


class TaskListModel(BaseModel):
    tasks: list[TaskModel]