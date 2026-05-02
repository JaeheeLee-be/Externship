from .dtos import InitialQNA

class CacheFactory:
    @staticmethod
    def create_initial_cache(
            category: str,
            title: str,
            content: str,
            answer: str,
    ):

        return InitialQNA(category=category, title=title, content=content, answer=answer)




