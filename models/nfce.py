# models/nfce.py
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship
from models.base import BaseModel

class NFCe(BaseModel):
    __tablename__ = 'nfce' 

    id = Column(Integer, primary_key=True, autoincrement=True)
    chave_acesso = Column(String(44), unique=True)
    fornecedor_id = Column(Integer, ForeignKey('fornecedores.id'))
    data_emissao = Column(DateTime, nullable=False)
    qrcode_url = Column(String(255), nullable=False)
    itens = relationship('ItemNFCe', backref='nfce', cascade='all, delete-orphan')