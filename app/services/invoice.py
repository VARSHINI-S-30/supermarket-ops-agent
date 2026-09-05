import os
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether
)

from app.database.db import SessionLocal
from app.database.models import (
    Bill,
    Product,
    Customer
)

from app.tools.preferences import get_preference


GENERATED_DIR = "generated"

IST = ZoneInfo(
    "Asia/Kolkata"
)


def _get_preference_value(key):
    """
    Retrieve one saved owner preference.
    """

    result = get_preference(key)

    if (
        result.get("success")
        and result.get("found")
    ):
        return result.get(
            "preference_value"
        )

    return None


def _get_shop_name():
    """
    Retrieve the configured shop name.

    Falls back to NEBULA SUPERMARKET.
    """

    shop_name = _get_preference_value(
        "shop_name"
    )

    if shop_name:
        return shop_name

    return "NEBULA SUPERMARKET"


def _get_gstin():
    """
    Retrieve configured GSTIN.
    """

    return _get_preference_value(
        "gstin"
    )


def generate_invoice(bill_id):
    """
    Generate a PDF invoice for a finalized bill.

    The invoice reads shop_name and GSTIN from
    persistent owner preferences.
    """

    db = SessionLocal()

    try:

        bill = (
            db.query(Bill)
            .filter(Bill.id == bill_id)
            .first()
        )

        if not bill:

            return {
                "success": False,
                "message": (
                    f"Bill #{bill_id} was not found."
                )
            }

        if bill.status != "finalized":

            return {
                "success": False,
                "message": (
                    f"Invoice can only be generated "
                    f"for finalized bills. "
                    f"Bill #{bill_id} is "
                    f"{bill.status}."
                )
            }

        os.makedirs(
            GENERATED_DIR,
            exist_ok=True
        )

        filename = (
            f"invoice_{bill.id}.pdf"
        )

        filepath = os.path.join(
            GENERATED_DIR,
            filename
        )

        shop_name = _get_shop_name()
        gstin = _get_gstin()

        created_at = bill.created_at

        if created_at:

            if created_at.tzinfo is None:

                created_at = created_at.replace(
                    tzinfo=IST
                )

            created_at = created_at.astimezone(
                IST
            )

            invoice_date = created_at.strftime(
                "%d-%m-%Y %I:%M %p"
            )

        else:

            invoice_date = datetime.now(
                IST
            ).strftime(
                "%d-%m-%Y %I:%M %p"
            )

        customer_name = "Walk-in Customer"

        if bill.customer_id:

            customer = (
                db.query(Customer)
                .filter(
                    Customer.id == bill.customer_id
                )
                .first()
            )

            if customer:

                customer_name = (
                    customer.name
                    or "Customer"
                )

        styles = getSampleStyleSheet()

        title_style = styles["Title"]
        title_style.fontSize = 20
        title_style.leading = 24

        normal_style = styles["Normal"]
        normal_style.fontSize = 9
        normal_style.leading = 12

        small_style = styles["Normal"]
        small_style.fontSize = 8
        small_style.leading = 10

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm
        )

        story = []

        # --------------------------------------------------
        # HEADER
        # --------------------------------------------------

        story.append(
            Paragraph(
                shop_name,
                title_style
            )
        )

        story.append(
            Paragraph(
                "SUPERMARKET INVOICE",
                styles["Heading2"]
            )
        )

        if gstin:

            story.append(
                Paragraph(
                    f"<b>GSTIN:</b> {gstin}",
                    normal_style
                )
            )

        story.append(
            Spacer(
                1,
                6 * mm
            )
        )

        # --------------------------------------------------
        # BILL INFORMATION
        # --------------------------------------------------

        bill_info = [
            [
                Paragraph(
                    "<b>Invoice No.</b>",
                    normal_style
                ),
                Paragraph(
                    f"#{bill.id}",
                    normal_style
                ),
                Paragraph(
                    "<b>Date</b>",
                    normal_style
                ),
                Paragraph(
                    invoice_date,
                    normal_style
                )
            ],
            [
                Paragraph(
                    "<b>Customer</b>",
                    normal_style
                ),
                Paragraph(
                    customer_name,
                    normal_style
                ),
                Paragraph(
                    "<b>Payment</b>",
                    normal_style
                ),
                Paragraph(
                    (
                        bill.payment_mode.upper()
                        if bill.payment_mode
                        else "-"
                    ),
                    normal_style
                )
            ]
        ]

        bill_table = Table(
            bill_info,
            colWidths=[
                28 * mm,
                55 * mm,
                28 * mm,
                55 * mm
            ]
        )

        bill_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),
                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
                    colors.lightgrey
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ])
        )

        story.append(
            bill_table
        )

        story.append(
            Spacer(
                1,
                6 * mm
            )
        )

        # --------------------------------------------------
        # ITEMS
        # --------------------------------------------------

        item_rows = [
            [
                "S.No.",
                "Product",
                "Qty",
                "Unit Price",
                "GST %",
                "GST",
                "Total"
            ]
        ]

        for index, item in enumerate(
            bill.items,
            start=1
        ):

            product = (
                db.query(Product)
                .filter(
                    Product.id == item.product_id
                )
                .first()
            )

            product_name = (
                product.name
                if product
                else "Unknown Product"
            )

            unit = (
                product.unit
                if product
                else ""
            )

            item_rows.append([
                str(index),
                f"{product_name} ({unit})",
                str(item.quantity),
                f"₹{Decimal(str(item.unit_price)):.2f}",
                f"{Decimal(str(item.gst_rate)):.2f}%",
                f"₹{Decimal(str(item.gst_amount)):.2f}",
                f"₹{Decimal(str(item.total_amount)):.2f}"
            ])

        item_table = Table(
            item_rows,
            colWidths=[
                12 * mm,
                55 * mm,
                18 * mm,
                25 * mm,
                18 * mm,
                23 * mm,
                25 * mm
            ],
            repeatRows=1
        )

        item_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "LEFT"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ])
        )

        story.append(
            item_table
        )

        story.append(
            Spacer(
                1,
                6 * mm
            )
        )

        # --------------------------------------------------
        # GST BREAKUP
        # --------------------------------------------------

        subtotal = Decimal(
            str(bill.subtotal)
        )

        gst_amount = Decimal(
            str(bill.gst_amount)
        )

        cgst = (
            gst_amount / Decimal("2")
        ).quantize(
            Decimal("0.01")
        )

        sgst = (
            gst_amount - cgst
        ).quantize(
            Decimal("0.01")
        )

        total = Decimal(
            str(bill.total_amount)
        )

        summary_rows = [
            [
                "Taxable Amount",
                f"₹{subtotal:.2f}"
            ],
            [
                "CGST",
                f"₹{cgst:.2f}"
            ],
            [
                "SGST",
                f"₹{sgst:.2f}"
            ],
            [
                "Total GST",
                f"₹{gst_amount:.2f}"
            ],
            [
                "Grand Total",
                f"₹{total:.2f}"
            ]
        ]

        summary_table = Table(
            summary_rows,
            colWidths=[
                45 * mm,
                40 * mm
            ],
            hAlign="RIGHT"
        )

        summary_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                ),
                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold"
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ])
        )

        story.append(
            summary_table
        )

        story.append(
            Spacer(
                1,
                8 * mm
            )
        )

        # --------------------------------------------------
        # CREDIT NOTE
        # --------------------------------------------------

        if bill.payment_mode == "credit":

            story.append(
                Paragraph(
                    (
                        "<b>Payment Note:</b> "
                        "This invoice was recorded as "
                        "credit/khata."
                    ),
                    normal_style
                )
            )

            story.append(
                Spacer(
                    1,
                    4 * mm
                )
            )

        # --------------------------------------------------
        # FOOTER
        # --------------------------------------------------

        story.append(
            Paragraph(
                "Thank you for shopping with us!",
                normal_style
            )
        )

        story.append(
            Spacer(
                1,
                2 * mm
            )
        )

        story.append(
            Paragraph(
                "Generated by Nebula Supermarket Ops Agent",
                small_style
            )
        )

        doc.build(
            story
        )

        return {
            "success": True,
            "bill_id": bill.id,
            "filepath": filepath,
            "filename": filename,
            "shop_name": shop_name,
            "gstin": gstin,
            "message": (
                f"Invoice for bill #{bill.id} "
                "generated successfully."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "message": (
                f"Error generating invoice: {str(e)}"
            )
        }

    finally:

        db.close()