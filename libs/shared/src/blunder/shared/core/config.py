from dotenv import find_dotenv
from pydantic_settings import BaseSettings as PydanticSettings
from pydantic_settings import SettingsConfigDict


class BaseSettings(PydanticSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__", env_file=find_dotenv(), extra="ignore")
