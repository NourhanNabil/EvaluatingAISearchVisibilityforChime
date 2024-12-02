class StringUtils:
    @classmethod
    def is_None_or_whitespace(cls, input:str):
        return (input is None) or (len(input.strip()) < 1)


