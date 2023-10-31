import datetime
import os
import sys
from typing import Self, cast

import nfc  # type: ignore[import]
import requests
from nfc.tag import TagCommandError  # type: ignore[import]
from nfc.tag.tt3 import BlockCode, ServiceCode, Type3Tag  # type: ignore[import]
from nfc.tag.tt3_sony import FelicaStandard  # type: ignore[import]
from playsound import playsound
from rich.console import Console

console = Console(record=True)

SYSTEM_NAME = "Tokyo University of Science student ID card"
SYSTEM_CODE = 0x8A0F
ENDPOINT_URL = os.environ.get("ENDPOINT_URL")
SUCCESS_SOUND_PATH = os.environ.get("SUCCESS_SOUND_PATH")

if ENDPOINT_URL is None:
    console.print(
        "[bold bright_yellow]WARNING",
        "[white]The environment variable [bold]ENDPOINT_URL[/bold] is not set.",
        sep="\t",
    )
if SUCCESS_SOUND_PATH is None:
    console.print(
        "[bold bright_yellow]WARNING",
        "[white]The environment variable [bold]SUCCESS_SOUND_PATH[/bold] is not set.",
        sep="\t",
    )


class CardReader:
    clf: nfc.ContactlessFrontend

    def __init__(self: Self) -> None:
        try:
            try:
                self.clf = nfc.ContactlessFrontend("usb")
            except Exception:
                raise
        except Exception:
            console.print_exception()

    def read(self: Self) -> None:
        console.print("[bold green]Hold your student ID card on the card reader...")
        try:
            while True:
                self.clf.connect(rdwr={"on-connect": self.__on_connect, "on-release": self.__on_release})
        except Exception:  # Ctrl+C
            console.save_html(f"./log/log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.html")
            sys.exit(0)

    def __on_connect(self: Self, tag: nfc.tag.Tag) -> bool:
        console.log(
            "[bold bright_cyan]INFO",
            f"Connected to the card with Manufacture ID of [underline]{tag.identifier.hex().upper()}[/underline].",
            sep="\t",
        )
        try:
            try:
                self.__dump_tag(tag)
                if isinstance(tag, FelicaStandard) and SYSTEM_CODE in tag.request_system_code():
                    tag.idm, tag.pmm, *_ = tag.polling(0xFE00)
                    student_id = self.__get_student_id(tag)
                    student_name = self.__get_student_name(tag)
                    console.log(
                        "[bold bright_green]SUCCESS",
                        "Read the card information.",
                        sep="\t",
                    )
                    console.log(
                        "",
                        f"[b]Student ID:[/b] [white underline not b]{student_id}",
                        f"[b]Student Name:[/b] [white underline not b]{student_name}",
                        sep="\t",
                    )
                    if ENDPOINT_URL is not None:
                        try:
                            requests.post(
                                ENDPOINT_URL,
                                json={"student_id": student_id},
                                timeout=6,
                            )
                        except requests.exceptions.ConnectionError:
                            console.log(
                                "[bold bright_red]ERROR",
                                "[white]Failed to connect to the server.",
                                sep="\t",
                            )
                        except requests.exceptions.RequestException:
                            console.log(
                                "[bold bright_red]ERROR",
                                "[white]Failed to send data to the server.",
                                sep="\t",
                            )
                        else:
                            console.log(
                                "[bold bright_green]SUCCESS",
                                "[white]Sent data to the server.",
                                sep="\t",
                            )
                            if SUCCESS_SOUND_PATH is not None:
                                playsound(SUCCESS_SOUND_PATH, block=False)
                else:
                    console.log(
                        "[bold bright_red]ERROR",
                        f"[white]The card is not {SYSTEM_NAME}.",
                        sep="\t",
                    )
            except Exception as e:
                if issubclass(type(e), TagCommandError):
                    console.log(
                        "[bold bright_red]ERROR",
                        "[white]The card left the card reader during the reading process.",
                        sep="\t",
                    )

                else:
                    raise
        except Exception:
            console.print_exception()

        return True

    def __on_release(self: Self, tag: nfc.tag.Tag) -> None:
        console.log(
            "[bold bright_cyan]INFO",
            f"Released to the card with Manufacture ID of [underline]{tag.identifier.hex().upper()}[/underline].",
            sep="\t",
        )

    def __read_data_block(self: Self, tag: Type3Tag, service_code_number: int, block_code_number: int) -> bytearray:
        service_code = ServiceCode(service_code_number, 0b001011)
        block_code = BlockCode(block_code_number)
        return cast(bytearray, tag.read_without_encryption([service_code], [block_code]))

    def __get_student_id(self: Self, tag: Type3Tag) -> str:
        # Random Service 106: write with key & read w/o key (0x1A88 0x1A8B)
        # 0x00000:
        student_id_bytearray = self.__read_data_block(tag, 106, 0)
        role_classification = student_id_bytearray.decode("shift_jis")[0:2]
        match role_classification:
            case "01" | "02":  # student
                return student_id_bytearray.decode("shift_jis")[2:9]
            case "11":  # faculty
                return student_id_bytearray.decode("shift_jis")[2:8]
            case _:  # unknown
                msg = f"Unknown role classification: {role_classification}"
                raise Exception(msg)

    def __get_student_name(self: Self, tag: Type3Tag) -> str:
        # Random Service 106: write with key & read w/o key (0x1A88 0x1A8B)
        # 0x00010:
        student_name_bytearray = self.__read_data_block(tag, 106, 1)
        return student_name_bytearray.decode("shift_jis")[0:16]

    def __dump_tag(self: Self, tag: nfc.tag.Tag) -> str:
        return "\n".join(tag.dump())


if __name__ == "__main__":
    card_reader = CardReader()
    card_reader.read()
