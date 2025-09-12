import frappe
import oci
import uuid
import urllib.parse

def get_oci_client():
    tenancy_ocid = frappe.conf.get("oci_tenancy_ocid")
    user_ocid = frappe.conf.get("oci_user_ocid")
    fingerprint = frappe.conf.get("oci_fingerprint")
    key_content = frappe.conf.get("oci_key_content").replace("\\n", "\n")
    region = frappe.conf.get("oci_region")

    if not all([tenancy_ocid, user_ocid, fingerprint, key_content, region]):
        raise Exception("Missing required OCI configuration in site_config.json")

    config = {
        "user": user_ocid,
        "key_content": key_content,
        "fingerprint": fingerprint,
        "tenancy": tenancy_ocid,
        "region": region,
    }

    return oci.object_storage.ObjectStorageClient(config)

def upload_pdf_to_oracle(file, folder_name=None, material_name=None):
    """
    Upload a PDF file to Oracle Object Storage
    - file: dict with {"filename": str, "content": bytes}
    - folder_name: optional folder override, else from site_config
    - material_name: optional string to prefix in filename
    """
    client = get_oci_client()
    namespace = client.get_namespace().data
    bucket_name = frappe.conf.get("oci_bucket_name")

    if not bucket_name:
        raise Exception("Missing oci_bucket_name in site_config.json")

    # Get folder from param or site_config
    folder = folder_name or frappe.conf.get("oci_materials_folder")
    if not folder:
        raise Exception("Missing oci_materials_folder in site_config.json")

    # Sanitize material_name for filenames
    safe_name = (material_name or "Material").replace(" ", "_")

    # Force file naming format → <safe_name>-<uuid>.pdf
    object_name = f"{folder}/{safe_name}-{uuid.uuid4()}.pdf"

    filedata = file.get("content")
    if not filedata:
        raise Exception("No file content provided")

    client.put_object(
        namespace,
        bucket_name,
        object_name,
        filedata,
        content_type="application/pdf",
        content_disposition="inline",
        opc_meta={"oracle-soc-public-read": "true"},
    )

    file_url = (
        f"https://objectstorage.{frappe.conf.get('oci_region')}.oraclecloud.com"
        f"/n/{namespace}/b/{bucket_name}/o/{urllib.parse.quote(object_name)}"
    )

    return {"fileUrl": file_url, "objectName": object_name}
