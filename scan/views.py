import re
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.contrib import messages
import os
import uuid
import json

from nutri.models import NutriUser
from nutriscan import settings
from .services import barcode_scanner, product_lookup, nutrition
from .models import ProductScan
from .forms import ScanForm


def scan_product_ajax(request):
    """
    Handles the AJAX request for scanning a product image.
    It uploads the image, stores its filename, and returns a JSON response
    with the status and image URL.
    """
    if request.method == 'POST':
        form = ScanForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                if 'user_id' not in request.session:
                    return JsonResponse({
                        "status": "error",
                        "message": "Please log in first.",
                        "redirect_url": "/nutri/login/"
                    })

                image = form.cleaned_data.get('image')
                if not image:
                    return JsonResponse({"status": "error", "message": "No image uploaded."})

                fs = FileSystemStorage(
                    location=os.path.join(settings.MEDIA_ROOT, 'scans'),
                    base_url=f"{settings.MEDIA_URL}scans/"
                )

                original_filename = image.name
                unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                filename = fs.save(unique_filename, image)

                request.session['uploaded_filename'] = filename

                return JsonResponse({
                    "status": "success",
                    "filename": filename,
                    "image_url": fs.url(filename)
                })

            except Exception as e:
                return JsonResponse({"status": "error", "message": f"Upload failed: {str(e)}"})

        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid form data.",
                "errors": form.errors.as_json()
            })

    else:
        form = ScanForm()
        return render(request, 'scan/scan.html', {'form': form})


def scan_loading_view(request, filename):
    """
    Renders a loading page after the image is uploaded.
    It displays the uploaded image to the user while the processing happens.
    """
    fs = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'scans'),
        base_url=f"{settings.MEDIA_URL}scans/"
    )
    return render(request, 'scan/scan_loading.html', {
        'filename': filename,
        'image_url': fs.url(filename)
    })


def process_scan(request, filename):
    """
    Processes uploaded image, scans barcode, analyzes product, and stores results in session.
    """
    if 'user_id' not in request.session:
        return JsonResponse({"status": "error", "message": "User not logged in."})

    fs = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'scans'),
        base_url=f"{settings.MEDIA_URL}scans/"
    )
    image_path = fs.path(filename)

    try:
        barcode = barcode_scanner.scan_barcode(image_path)
        if not barcode:
            return JsonResponse({"status": "error", "message": "No barcode detected in the image."})

        product = product_lookup.fetch_product_data(barcode)
        if not product:
            return JsonResponse({"status": "error", "message": "Product not found in database."})

        product['nutriments'] = product.get('nutriments', {})

        try:
            user = NutriUser.objects.get(id=request.session['user_id'])
        except NutriUser.DoesNotExist:
            if fs.exists(filename):
                fs.delete(filename)
            return JsonResponse({"status": "error", "message": "User not found."})

        pdf_path = 'healthy-diet-fact-sheet-394.pdf'
        
        response = nutrition.analyze_nutrition(
            age=user.age,
            weight=user.weight,
            height=user.height,
            bmi=user.bmi,
            health_conditions=user.health_conditions,
            dietary_preferences=user.dietary_preferences,
            goal=user.goal,
            product_info=product,
            pdf_path=pdf_path
        )
        print("Response type:", type(response))
        print("Response value:", response)


# Extract JSON-like part from response
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                extracted_data = json.loads(match.group())
                advisability = extracted_data.get('advisability', 'Unknown')
                summary = extracted_data.get('summary', 'No summary provided.')
            except json.JSONDecodeError:
                advisability = 'Error'
                summary = 'Could not parse summary.'
        else:
             advisability = 'Not found'
             summary = 'Could not extract JSON block.'
        

        default_nutrients = {
            'energy': 0, 'energy-kcal': 0, 'energy-kj': 0,
            'fat': 0, 'saturated-fat': 0,
            'carbohydrates': 0, 'sugars': 0,
            'fiber': 0, 'proteins': 0,
            'salt': 0, 'sodium': 0
        }
        product['nutriments'] = {**default_nutrients, **product.get('nutriments', {})}

        nutrient_map = (
            "energy:Energy (kcal)|energy-kcal:Energy (kcal)|energy-kj:Energy (kJ)|"
            "fat:Total Fat|saturated-fat:Saturated Fat|trans-fat:Trans Fat|"
            "monounsaturated-fat:Monounsaturated Fat|polyunsaturated-fat:Polyunsaturated Fat|"
            "cholesterol:Cholesterol|carbohydrates:Total Carbohydrates|"
            "dietary-fiber:Dietary Fiber|soluble-fiber:Soluble Fiber|"
            "insoluble-fiber:Insoluble Fiber|sugars:Total Sugars|"
            "added-sugars:Added Sugars|sugar-alcohols:Sugar Alcohols|"
            "protein:Protein|salt:Salt|sodium:Sodium|potassium:Potassium|"
            "calcium:Calcium|iron:Iron|vitamin-a:Vitamin A|vitamin-c:Vitamin C|"
            "vitamin-d:Vitamin D|vitamin-e:Vitamin E|vitamin-k:Vitamin K|"
            "thiamin:Thiamin (B1)|riboflavin:Riboflavin (B2)|niacin:Niacin (B3)|"
            "vitamin-b6:Vitamin B6|folate:Folate (B9)|vitamin-b12:Vitamin B12|"
            "biotin:Biotin (B7)|pantothenic-acid:Pantothenic Acid (B5)|"
            "phosphorus:Phosphorus|iodine:Iodine|magnesium:Magnesium|"
            "zinc:Zinc|selenium:Selenium|copper:Copper|manganese:Manganese|"
            "chromium:Chromium|molybdenum:Molybdenum|chloride:Chloride|"
            "omega-3:Omega-3 Fatty Acids|omega-6:Omega-6 Fatty Acids|"
            "alanine:Alanine|arginine:Arginine|aspartic-acid:Aspartic Acid|"
            "glutamic-acid:Glutamic Acid|glycine:Glycine|histidine:Histidine|"
            "hydroxyproline:Hydroxyproline|isoleucine:Isoleucine|leucine:Leucine|"
            "lysine:Lysine|methionine:Methionine|phenylalanine:Phenylalanine|"
            "proline:Proline|serine:Serine|threonine:Threonine|"
            "tryptophan:Tryptophan|tyrosine:Tyrosine|valine:Valine|"
            "caffeine:Caffeine|alcohol:Alcohol|water:Water Content|"
            "ash:Ash Content|ph:pH Level|pral:PRAL (Renal Acid Load)|"
            "gluten:Gluten|lactose:Lactose|fructose:Fructose|"
            "sucrose:Sucrose|starch:Starch|polyols:Polyols|"
            "gout-inducing:Gout-Inducing Purines|oxalate:Oxalate Content|"
            "phytate:Phytate Content"
        )

        request.session['latest_scan_results'] = {
    "product": product,
    "analysis": {
        "advisability": advisability,
        "summary": summary,
    },
    "nutrient_map": nutrient_map
}

        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


def result(request):
    """
    Displays scan result and cleans up uploaded image from storage.
    """
    scan_results = request.session.get('latest_scan_results')
    if not scan_results:
        messages.info(request, "No recent scan results found.")
        return redirect('scan')
    # Process summary into points
    if scan_results.get('analysis', {}).get('summary'):
        summary_points = [
            point.strip() 
            for point in scan_results['analysis']['summary'].split('.') 
            if point.strip()
        ]
    else:
        summary_points = []

    uploaded_filename = request.session.pop('uploaded_filename', None)
    if uploaded_filename:
        fs = FileSystemStorage(
            location=os.path.join(settings.MEDIA_ROOT, 'scans'),
            base_url=f"{settings.MEDIA_URL}scans/"
        )
        if fs.exists(uploaded_filename):
            fs.delete(uploaded_filename)

    return render(request, 'scan/result.html', {
        'product': scan_results.get('product'),
        'analysis': scan_results.get('analysis'),
        'nutrient_map': scan_results.get('nutrient_map'),
        'summary_points': summary_points,
    })
