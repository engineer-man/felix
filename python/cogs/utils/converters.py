from typing import Optional

from discord.ext.commands import BadArgument, Converter

ALLOWED_CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ!?'`-"
UNICODE_CHARACTERS = '𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹ǃ？’’-'


class OffTopicName(Converter):
    """A converter that ensures an added off-topic name is valid."""

    @classmethod
    def translate_name(cls, name: str = None, *, from_unicode: bool = True) -> Optional[str]:
        if not name:
            return None
        if from_unicode:
            table = str.maketrans(ALLOWED_CHARACTERS, UNICODE_CHARACTERS)
        else:
            table = str.maketrans(UNICODE_CHARACTERS, ALLOWED_CHARACTERS)

        return name.translate(table)

    async def convert(self, ctx, argument: str) -> str:
        # Chain multiple words to a single one
        argument = "-".join(argument.split())

        if not (2 <= len(argument) <= 96):
            raise BadArgument("Channel name must be between 2 and 96 chars long")

        elif not all(c.isalnum() or c in ALLOWED_CHARACTERS for c in argument):
            raise BadArgument(
                "Channel name must only consist of "
                "alphanumeric characters, minus signs or apostrophes."
            )

        # Replace invalid characters with unicode alternatives.
        return self.translate_name(argument)
