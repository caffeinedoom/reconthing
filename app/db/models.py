# app/db/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Subdomain(Base):
    __tablename__ = "subdomains"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, index=True)
    subdomain = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    dns_resolutions = relationship("DNSResolution", back_populates="subdomain")
    http_probe_results = relationship("HTTPProbeResult", back_populates="subdomain")

    __table_args__ = (UniqueConstraint('domain', 'subdomain', name='uix_domain_subdomain'),)


class DNSResolution(Base):
    __tablename__ = "dns_resolutions"

    id = Column(Integer, primary_key=True, index=True)
    subdomain_id = Column(Integer, ForeignKey('subdomains.id'), index=True)
    resolved_domain = Column(String, index=True)
    ip_address = Column(String)
    ttl = Column(Integer)
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subdomain = relationship("Subdomain", back_populates="dns_resolutions")

    __table_args__ = (UniqueConstraint('subdomain_id', 'resolved_domain', name='uix_subdomain_resolved_domain'),)

class HTTPProbeResult(Base):
    __tablename__ = "http_probe_results"

    id = Column(Integer, primary_key=True, index=True)
    subdomain_id = Column(Integer, ForeignKey('subdomains.id'), index=True)
    url = Column(String, index=True)
    status_code = Column(Integer)
    title = Column(String)
    content_length = Column(Integer)
    technologies = Column(JSON)
    webserver = Column(String)
    cdn_name = Column(String)
    cdn_type = Column(String)
    ip_address = Column(String)
    response_time = Column(String)
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subdomain = relationship("Subdomain", back_populates="http_probe_results")

    __table_args__ = (UniqueConstraint('subdomain_id', 'url', name='uix_subdomain_url'),)