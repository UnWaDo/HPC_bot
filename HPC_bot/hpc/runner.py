import re
import shlex
from typing import Any, Dict, List
from pydantic import BaseModel, Field, FieldValidationInfo, field_validator


class Runner(BaseModel):
    program: str
    allowed_args: List[str] = []
    default_args: List[str] = Field([], validate_default=True)

    associations: List[str] = []
    description: str = ''

    @staticmethod
    def _validate_args(args: List[str], allowed_args: List[str] = []):
        for arg in args:
            if not any(re.fullmatch(r, arg) for r in allowed_args):
                raise ValueError(
                    f'Argument {arg} is not in the list of allowed arguments')

    def validate_args(self, args: List[str]):
        Runner._validate_args(args, self.allowed_args)

    @field_validator('default_args')
    @classmethod
    def get_default_command(
            cls, field: List[str], info: FieldValidationInfo) -> str:
        if 'allowed_args' not in info.data:
            raise ValueError(
                'Require allowed_args to validate default_command')

        if len(field) == 0:
            if '{}' in info.data['allowed_args']:
                return ['{}']

            return []

        Runner._validate_args(field, info.data['allowed_args'])
        return field

    def create_command(self, args: List[str] = None,
                       filename: str = '') -> str:
        if args is not None:
            self.validate_args(args)
        else:
            args = self.default_args.copy()

        if filename is None:
            filename = ''

        for i, arg in enumerate(args):
            if arg == '{}':
                args[i] = f"'{filename}'"
        return ' '.join([self.program] + args).strip()

    def split_command(self, command: str) -> List[str]:
        args = shlex.split(command)

        if len(args) < 1:
            raise ValueError(f'Empty command given')
        if args[0] != self.program:
            raise ValueError(
                f'Program name must be {self.program}, got {args[0]} instead')

        args = args[1:]
        self.validate_args(args)

        return args

    def __str__(self) -> str:
        description = self.description
        if description == '':
            description = 'описание отсутствует'

        allowed_args = '-'
        if len(self.allowed_args) > 0:
            allowed_args = ', '.join(self.allowed_args)

        default_args = '-'
        if len(self.default_args) > 0:
            default_args = ', '.join(self.default_args)

        associations = '-'
        if len(self.associations) > 0:
            associations = ', '.join(self.associations)

        return (
            '<b>{program}</b>: {description}; '
            'доступные аргументы: {allowed_args}; '
            'стандартные аргументы: {default_args}; '
            'ассоциируется с расширениями: {associations}'
        ).format(
            program=self.program,
            description=description,
            allowed_args=allowed_args,
            default_args=default_args,
            associations=associations
        )
