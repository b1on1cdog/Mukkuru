# Copyright (c) 2025 b1on1cdog
# Licensed under the MIT License
''' license controller module '''
import os
from pathlib import Path
from flask import Blueprint, jsonify
from utils.core import APP_DIR, backend_log

license_controller = Blueprint('license', __name__)

@license_controller.route("/license")
def get_licenses():
    """ Get third-party licenses """
    licenses = {}
    license_dir = os.path.join(APP_DIR, "docs", "license")
    backend_log(license_dir)
    license_files = list(Path(license_dir).glob("*.txt"))
    for license_file in license_files:
        product_name = license_file.name.replace(".txt", "")
        licenses[product_name] = license_file.resolve().read_text()
    return jsonify(licenses)
