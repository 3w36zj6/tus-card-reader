import datetime
import sys
from typing import Self, cast

import nfc  # type: ignore
from nfc.tag import TagCommandError  # type: ignore
from nfc.tag.tt3 import BlockCode, ServiceCode, Type3Tag  # type: ignore
from nfc.tag.tt3_sony import FelicaStandard  # type: ignore
from rich.console import Console

SYSTEM_NAME = "Tokyo University of Science student ID card"
SYSTEM_CODE = 0x8A0F

console = Console(record=True)


class CardReader:
    clf: nfc.ContactlessFrontend

    def __init__(self: Self) -> None:
        try:
            try:
                self.clf = nfc.ContactlessFrontend("usb")
            except Exception as e:
                raise e
        except Exception:
            console.print_exception()

    def read(self: Self) -> None:
        console.print("[bold green]Hold your student ID card on the card reader...")
        try:
            while True:
                self.clf.connect(
                    rdwr={
                        "on-connect": self.__on_connect,
                        "on-release": self.__on_release,
                        "iterations": 1,
                    }
                )
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
                    raise e
        except Exception:
            console.print_exception()

        return True

    def __on_release(self: Self, tag: nfc.tag.Tag) -> None:
        console.log(
            "[bold bright_cyan]INFO",
            f"Released to the card with Manufacture ID of [underline]{tag.identifier.hex().upper()}[/underline].",
            sep="\t",
        )

    def __read_data_block(self: Self, tag: Type3Tag, service_code: ServiceCode, block_code: BlockCode) -> bytearray:
        service_code = ServiceCode(service_code, 0b001011)
        block_code = BlockCode(block_code)
        read_bytearray = cast(bytearray, tag.read_without_encryption([service_code], [block_code]))
        return read_bytearray

    def __get_student_id(self: Self, tag: Type3Tag) -> str:
        # Random Service 106: write with key & read w/o key (0x1A88 0x1A8B)
        # 0x00000:
        student_id_bytearray = self.__read_data_block(tag, cast(ServiceCode, 106), cast(BlockCode, 0))
        role_classification = student_id_bytearray.decode("shift_jis")[0:2]
        match role_classification:
            case "01" | "02":  # student
                return student_id_bytearray.decode("shift_jis")[2:9]
            case "11":  # faculty
                return student_id_bytearray.decode("shift_jis")[2:8]
            case _:  # unknown
                raise Exception(f"Unknown role classification: {role_classification}")

    def __get_student_name(self: Self, tag: Type3Tag) -> str:
        # Random Service 106: write with key & read w/o key (0x1A88 0x1A8B)
        # 0x00010:
        student_name_bytearray = self.__read_data_block(tag, cast(ServiceCode, 106), cast(BlockCode, 1))
        return student_name_bytearray.decode("shift_jis")[0:16]

    def __dump_tag(self: Self, tag: nfc.tag.Tag) -> str:
        return "\n".join(tag.dump())


if __name__ == "__main__":
    card_reader = CardReader()
    card_reader.read()
