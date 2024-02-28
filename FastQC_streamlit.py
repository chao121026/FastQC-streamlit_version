import streamlit as st
import subprocess
import os
import base64
from datetime import datetime
import multiprocessing


# Function to run FastQC analysis
def run_fastqc(input_file):
    # Create a directory to store FastQC output
    output_dir = "fastqc_output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate a unique filename based on timestamp and original filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{input_file.name}"
    temp_file_path = os.path.join(output_dir, unique_filename)

    # Save the uploaded file to the temporary location
    with open(temp_file_path, "wb") as f:
        f.write(input_file.getbuffer())

    # Run FastQC command
    cmd = f"fastqc {temp_file_path} -o {output_dir}"
    st.write(f"Running FastQC command: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True)
        st.success("FastQC analysis completed successfully!")
        return output_dir, unique_filename
    except subprocess.CalledProcessError as e:
        st.error(f"Error running FastQC: {e}")
        return None, None


# Function to generate a download link for a file
def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href


# Function to upload file chunk to remote server using multiprocessing
def upload_file_chunk(uploaded_file, chunk_start, chunk_size, result_queue):
    try:
        # Create a temporary file to store the chunk
        with open(f"temp_{chunk_start}.fastq", "wb") as f:
            f.write(uploaded_file.read(chunk_size))

        result_queue.put(True)
    except Exception as e:
        result_queue.put(False)


# Main function
def main():
    st.title("FastQC Analysis")

    st.write(
        "Welcome to the FastQC Analysis application! This tool allows you to quickly assess the quality of your sequencing data using FastQC."
        "Please follow the instructions below:"
    )

    # File upload section
    st.header("Step 1: Upload Sequencing Data")
    st.write(
        "Upload your sequencing data file (e.g., FASTQ format) using the file uploader below."
        "You can drag and drop your file or click the 'Browse files' button."
    )
    uploaded_file = st.file_uploader("Upload FASTQ File", type=["fastq", "fq"])

    # Run FastQC analysis when file is uploaded
    if uploaded_file:
        st.write("File uploaded successfully!")
        st.write("Starting FastQC analysis...")

        # Define chunk size (1MB)
        chunk_size = 100 * 1024 * 1024

        # Read file contents into memory
        file_contents = uploaded_file.read()

        # Create result queue
        result_queue = multiprocessing.Queue()

        # Create processes for uploading chunks
        processes = []
        for chunk_start in range(0, len(file_contents), chunk_size):
            process = multiprocessing.Process(target=upload_file_chunk,
                                              args=(uploaded_file, chunk_start, chunk_size, result_queue))
            processes.append(process)
            process.start()

        # Wait for all processes to finish
        for process in processes:
            process.join()

        # Check if all chunks were uploaded successfully
        if all(result_queue.get() for _ in range(len(processes))):
            st.write("File chunks uploaded successfully!")

            # Run FastQC analysis
            output_dir, unique_filename = run_fastqc(uploaded_file)
            if output_dir and unique_filename:
                st.write("FastQC analysis completed successfully! You can download the report using the link below:")
                report_path = os.path.join(output_dir, f"{unique_filename.split('.')[0]}_fastqc.html")
                st.markdown(get_binary_file_downloader_html(report_path, 'FastQC Report'), unsafe_allow_html=True)
        else:
            st.error("Failed to upload file chunks.")


if __name__ == "__main__":
    main()
