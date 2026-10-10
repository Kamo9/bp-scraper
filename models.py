from database import Base

from typing import Optional
from sqlalchemy import Column, BigInteger, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
class StrangeWeapon(Base):
	__tablename__ = "weapons";

	id: Mapped[int] = mapped_column(primary_key=True);
	steamid: Mapped[str] = mapped_column(String(17));
	timestamp: Mapped[int];
	original_id: Mapped[str];
	name: Mapped[str];
	strange_count_name: Mapped[str];
	strange_count: Mapped[int];
	part1_name: Mapped[Optional[str]];
	part1_count: Mapped[Optional[int]];
	part2_name: Mapped[Optional[str]];
	part2_count: Mapped[Optional[int]];
	part3_name: Mapped[Optional[str]];
	part3_count: Mapped[Optional[int]];

	def __repr__(self) -> str:
		return f"{self.id}, {self.steamid}, {self.timestamp}: {self.name}, {strange_count} {strange_count_name}";
		