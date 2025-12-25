export async function downloadPdfFile(downloadUrl, filename) {
  if (!downloadUrl) throw new Error('Missing download URL');
  const response = await fetch(downloadUrl);
  if (!response.ok) {
    throw new Error('Download failed');
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename || '';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}
