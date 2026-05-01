from django.shortcuts import render, redirect
from pymongo import MongoClient

client = MongoClient("mongodb+srv://britesamsekar:Brite%4012@cluster0.sjxgiqy.mongodb.net/")
db = client["water_billing"]
collection = db["customers"]

def login(request):
    if request.method == "POST":
        if request.POST.get("password") == "brite":
            return redirect("dashboard")
        else:
            return render(request, "login.html", {"error": "Wrong Password"})
    return render(request, "login.html")


def dashboard(request):
    data = list(collection.find())

    names = []
    usage = []
    area_data = {}

    for d in data:
        name = d.get("customer_name", d.get("name", "Unknown"))
        names.append(name)

        u = d.get("units", 0)
        usage.append(u)

        area = d.get("area", "Unknown")
        area_data[area] = area_data.get(area, 0) + u

    return render(request, "dashboard.html", {
        "names": names,
        "usage": usage,
        "areas": list(area_data.keys()),
        "area_usage": list(area_data.values())
    })


def add_customer(request):
    if request.method == "POST":

        cid = request.POST["cid"]
        name = request.POST["name"]
        area = request.POST["area"]
        liters = int(request.POST["liters"])
        month = request.POST["month"]
        year = int(request.POST["year"])

        units = liters // 1000

        if units <= 50:
            bill = units * 2
        elif units <= 100:
            bill = units * 3
        else:
            bill = units * 5
        if not cid or not name or not area:
            return render(request, "add.html", {
                "error": "All fields are required!"
            })
        
        collection.insert_one({
            "customer_id": str(cid),
            "customer_name": name,
            "area": area,
            "month": month,
            "year": year,
            "water_used_liters": liters,
            "units": units,
            "bill_amount": bill,
            "category": "Residential",
            "payment_status": "Pending"
        })

        return redirect("view")

    return render(request, "add.html")


def view_customers(request):
    query = request.GET.get("q")
    month = request.GET.get("month")

    filter_query = {}

    # 🔍 SEARCH BY NAME OR ID
    if query:
        filter_query["$or"] = [
            {"customer_name": {"$regex": query, "$options": "i"}},
            {"customer_id": {"$regex": query, "$options": "i"}}
        ]

    # 📅 FILTER BY MONTH
    if month:
        filter_query["month"] = month

    data = list(collection.find(filter_query))

    return render(request, "view.html", {"data": data})

from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from datetime import datetime

def download_bill(request, cid):
    d = collection.find_one({"customer_id": str(cid)})

    if not d:
        return HttpResponse("Customer not found ❌")

    # ===== BILL CALCULATION =====
    u = d["units"]
    bill = u*2 if u<=50 else u*3 if u<=100 else u*5

    # ===== DUE DATE CALCULATION =====
    month_map = {
        "Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
        "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12
    }

    m = month_map[d["month"]]
    y = d["year"]

    if m == 12:
        m = 1
        y += 1
    else:
        m += 1

    due_date = datetime(y, m, 10).strftime("%d-%m-%Y")

    # ===== PDF RESPONSE =====
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bill_{cid}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)

    # ===== HEADER =====
    p.setFont("Helvetica-Bold", 18)
    p.drawString(180, 750, "WATER BILL REPORT")

    # ===== LINE =====
    p.setStrokeColor(colors.grey)
    p.line(50, 735, 550, 735)

    # ===== DETAILS =====
    p.setFont("Helvetica", 12)

    y_pos = 700
    gap = 25

    p.drawString(60, y_pos, f"Customer ID: {d['customer_id']}")
    y_pos -= gap

    p.drawString(60, y_pos, f"Name: {d['customer_name']}")
    y_pos -= gap

    p.drawString(60, y_pos, f"Area: {d['area']}")
    y_pos -= gap

    p.drawString(60, y_pos, f"Month: {d['month']} {d['year']}")
    y_pos -= gap

    p.drawString(60, y_pos, f"Water Used: {d['water_used_liters']} liters")
    y_pos -= gap

    p.drawString(60, y_pos, f"Units: {u}")
    y_pos -= gap

    p.drawString(60, y_pos, f"Total Bill: ₹{bill}")
    y_pos -= gap

    # ===== STATUS =====
    status = d.get("payment_status", "Pending")

    if status == "Paid":
        p.setFillColor(colors.green)
    else:
        p.setFillColor(colors.red)

    p.drawString(60, y_pos, f"Payment Status: {status}")
    p.setFillColor(colors.black)
    y_pos -= gap

    # ===== DUE DATE =====
    p.drawString(60, y_pos, f"Due Date: {due_date}")

    # ===== FOOTER =====
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(150, 100, "Thank you for using our Water Billing System")

    p.showPage()
    p.save()

    return response

def login(request):
    if request.method == "POST":
        login_type = request.POST.get("type")

        if login_type == "admin":
            password = request.POST.get("password")

            if password == "brite":
                return redirect("dashboard")
            else:
                return render(request, "login.html", {"error": "Wrong Admin Password"})

        elif login_type == "user":
            cid = request.POST.get("cid")

            if collection.find_one({"customer_id": str(cid)}):
                return redirect(f"/user/{cid}/")
            else:
                return render(request, "login.html", {"error": "User ID not found"})

    return render(request, "login.html")

def user_view(request, cid):
    data = list(collection.find({"customer_id": str(cid)}))

    if not data:
        return HttpResponse("User not found")

    months = []
    usage = []

    for d in data:
        months.append(d.get("month", ""))
        usage.append(d.get("units", 0))

    return render(request, "user.html", {
        "data": data,
        "months": months,
        "usage": usage
    })

def delete_customer(request, cid):
    collection.delete_one({"customer_id": str(cid)})
    return redirect("view")

def edit_customer(request, cid):
    d = collection.find_one({"customer_id": str(cid)})

    if request.method == "POST":
        liters = int(request.POST["liters"])
        units = liters // 1000

        if units <= 50:
            bill = units * 2
        elif units <= 100:
            bill = units * 3
        else:
            bill = units * 5

        collection.update_one(
            {"customer_id": str(cid)},
            {"$set": {
                "customer_name": request.POST["name"],
                "area": request.POST["area"],
                "water_used_liters": liters,
                "units": units,
                "bill_amount": bill
            }}
        )
        return redirect("view")

    return render(request, "edit.html", {"d": d})

def pay_bill(request, cid):
    collection.update_one(
        {"customer_id": str(cid)},
        {"$set": {"payment_status": "Paid"}}
    )
    return redirect(f"/user/{cid}/")
