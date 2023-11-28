import json
import logging
from json import JSONDecodeError
from typing import Union, Optional


class JSONTextsEmpty(Exception):
    pass


def parse_texts(
    textsPath: str = "texts.json", keyword: Optional[str] = None
) -> Union[dict[str, str], str]:
    try:
        texts = open(textsPath)
        textDict = json.load(texts)
        if len(textDict) > 0:
            if not keyword:
                return textDict
            if isinstance(textDict, dict):
                text = textDict.get(keyword, None)
                if not text:
                    return f"This text was not found in the file - {textsPath}"
                return text
        else:
            raise JSONTextsEmpty

    except FileNotFoundError as exp:
        logging.exception(
            "The path to the file with the texts is specified incorrectly!",
            exc_info=exp,
        )

    except JSONDecodeError as exp:
        logging.exception("Error parsing a JSON file with texts!", exc_info=exp)

    except JSONTextsEmpty as exp:
        logging.exception("The text file is empty!", exc_info=exp)
