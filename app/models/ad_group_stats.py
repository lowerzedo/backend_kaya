from app import db
from sqlalchemy import BigInteger


class AdGroupStats(db.Model):
    __tablename__ = "ad_group_stats"
    id = db.Column(
        BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    date = db.Column(db.Date, nullable=False)
    ad_group_id = db.Column(
        db.BigInteger, db.ForeignKey("ad_group.ad_group_id"), nullable=False
    )
    device = db.Column(db.String(50), nullable=False)
    impressions = db.Column(db.Integer, nullable=False)
    clicks = db.Column(db.Integer, nullable=False)
    conversions = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)

    ad_group = db.relationship("AdGroup", backref=db.backref("stats", lazy=True))

    def serialize(self):
        return {
            "id": self.id,
            "date": self.date,
            "ad_group_id": self.ad_group_id,
            "device": self.device,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "cost": self.cost,
        }
