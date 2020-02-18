from abc import ABC, abstractmethod


class Agent(ABC):

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def act(self, event, target_object_type):
        pass
