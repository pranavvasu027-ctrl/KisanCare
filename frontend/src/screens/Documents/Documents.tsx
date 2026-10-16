import React, { useState, useEffect, useRef } from 'react';
import {
  FileText, Upload, Search, Download, Trash2, Filter,
  CheckCircle2, AlertCircle, Loader2, ExternalLink, FileSpreadsheet,
  FileCheck, ShieldCheck, Tag, Calendar, Database
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { supabase } from '../../services/supabase';

interface DocumentItem {
  id: string;
  name: string;
  category: 'Soil Health' | 'Land Records' | 'Lab Reports' | 'Invoices & Schemes';
  size: string;
  uploadDate: string;
  status: 'Verified' | 'Extracted' | 'Pending' | 'Sample';
  storagePath?: string;
  isDemo?: boolean;
}

const DEMO_DOCUMENTS: DocumentItem[] = [
  {
    id: 'demo-doc-1',
    name: 'Soil_Health_Card_Field1_2025.pdf',
    category: 'Soil Health',
    size: '1.2 MB',
    uploadDate: '2025-06-15',
    status: 'Extracted',
    isDemo: true
  },
  {
    id: 'demo-doc-2',
    name: '7_12_Extract_Shirpur_Nashik.pdf',
    category: 'Land Records',
    size: '2.4 MB',
    uploadDate: '2025-01-10',
    status: 'Verified',
    isDemo: true
  },
  {
    id: 'demo-doc-3',
    name: 'Groundwater_Quality_Report_2025.pdf',
    category: 'Lab Reports',
    size: '850 KB',
    uploadDate: '2025-04-20',
    status: 'Extracted',
    isDemo: true
  },
  {
    id: 'demo-doc-4',
    name: 'PM_Kisan_Receipt_Installment_16.pdf',
    category: 'Invoices & Schemes',
    size: '420 KB',
    uploadDate: '2025-03-01',
    status: 'Sample',
    isDemo: true
  }
];

export default function Documents() {
  const { user, isDemoMode } = useAuth();
  const isAuthenticated = Boolean(user);

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const [uploadCategory, setUploadCategory] = useState<DocumentItem['category']>('Soil Health');
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user && isAuthenticated) {
      loadUserDocuments(user.id);
    } else {
      // In demo mode or when unauthenticated, load realistic sample documents
      setDocuments(DEMO_DOCUMENTS);
    }
  }, [user, isAuthenticated]);

  const loadUserDocuments = async (userId: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const { data, error } = await supabase
        .from('documents')
        .select('*')
        .eq('user_id', userId)
        .order('upload_timestamp', { ascending: false });

      if (error) {
        console.error('Failed to load documents:', error);
        setErrorMessage(`Database error: ${error.message}`);
        // A production read failure must not be presented as demo content.
        setDocuments([]);
        return;
      }

      if (data && data.length > 0) {
        const loaded: DocumentItem[] = data.map((d: any) => ({
          id: d.id,
          name: d.file_name,
          category: (d.category as any) || 'Soil Health',
          size: d.metadata?.size ? formatBytes(d.metadata.size) : 'File',
          uploadDate: d.upload_timestamp ? d.upload_timestamp.split('T')[0] : 'Recent',
          status: (d.extraction_status as any) || 'Verified',
          storagePath: d.storage_path,
          isDemo: false
        }));
        setDocuments(loaded);
      } else {
        // No uploaded documents yet; keep empty state or show helper
        setDocuments([]);
      }
    } catch (err: any) {
      console.error('Error in loadUserDocuments:', err);
      setErrorMessage(`Failed to fetch documents: ${err.message || String(err)}`);
    } finally {
      setIsLoading(false);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setErrorMessage(null);
    setStatusMessage(null);

    // File validation: Size limit (max 10MB)
    const MAX_FILE_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_FILE_SIZE) {
      setErrorMessage(`File size exceeds 10MB limit (Selected file size: ${formatBytes(file.size)}).`);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // File validation: Allowed formats
    const allowedExtensions = ['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'];
    const fileExt = file.name.split('.').pop()?.toLowerCase() || '';
    if (!allowedExtensions.includes(fileExt)) {
      setErrorMessage(`Unsupported file format (.${fileExt}). Please upload PDF, JPG, PNG, or DOC documents.`);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // If unauthenticated or demo mode without Supabase session
    if (!user || !isAuthenticated) {
      const newDemoDoc: DocumentItem[] = [{
        id: `demo-${Date.now()}`,
        name: file.name,
        category: uploadCategory,
        size: formatBytes(file.size),
        uploadDate: new Date().toISOString().split('T')[0],
        status: 'Sample',
        isDemo: true
      }, ...documents];
      setDocuments(newDemoDoc);
      setStatusMessage(`"${file.name}" received for current session. (Demo mode: File metadata stored in memory only).`);
      setTimeout(() => setStatusMessage(null), 5000);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // Authenticated Supabase Storage Upload
    setIsUploading(true);
    let uploadedPath: string | null = null;
    try {
      const sanitizedFileName = file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
      const storagePath = `${user.id}/${Date.now()}_${sanitizedFileName}`;

      // 1. Upload to Supabase Storage bucket 'farmer_documents'
      const { error: uploadError } = await supabase.storage
        .from('farmer_documents')
        .upload(storagePath, file, {
          contentType: file.type || 'application/octet-stream',
          upsert: false
        });

      if (uploadError) {
        throw new Error(`Storage upload error: ${uploadError.message}`);
      }
      uploadedPath = storagePath;

      // 2. Insert metadata into 'documents' table
      const { data: docData, error: dbError } = await supabase
        .from('documents')
        .insert({
          user_id: user.id,
          file_name: file.name,
          file_type: file.type || 'application/octet-stream',
          storage_path: storagePath,
          category: uploadCategory,
          provenance: 'FARMER_ENTERED',
          extraction_status: 'COMPLETED',
          metadata: { size: file.size, mimeType: file.type }
        })
        .select()
        .single();

      if (dbError) {
        const { error: cleanupError } = await supabase.storage
          .from('farmer_documents')
          .remove([storagePath]);
        const cleanupStatus = cleanupError
          ? ` Uploaded file cleanup also failed: ${cleanupError.message}`
          : ' Uploaded file was removed.';
        throw new Error(`Database record failed: ${dbError.message}.${cleanupStatus}`);
      }

      const newDoc: DocumentItem = {
        id: docData.id,
        name: docData.file_name,
        category: uploadCategory,
        size: formatBytes(file.size),
        uploadDate: new Date().toISOString().split('T')[0],
        status: 'Verified',
        storagePath: storagePath,
        isDemo: false
      };

      setDocuments([newDoc, ...documents]);
      setStatusMessage(`"${file.name}" uploaded successfully to secure storage!`);
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (err: any) {
      console.error('File upload failed:', err);
      setErrorMessage(`Upload failed: ${err.message || String(err)}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDownload = async (doc: DocumentItem) => {
    setErrorMessage(null);
    if (doc.isDemo || !doc.storagePath) {
      setStatusMessage(`Sample Document: "${doc.name}" is a demo record. File download is only available for real files uploaded with an authenticated account.`);
      setTimeout(() => setStatusMessage(null), 6000);
      return;
    }

    try {
      // Create a secure time-bounded signed URL (valid for 5 minutes)
      const { data, error } = await supabase.storage
        .from('farmer_documents')
        .createSignedUrl(doc.storagePath, 300);

      if (error || !data?.signedUrl) {
        throw new Error(error?.message || 'Could not generate download URL');
      }

      window.open(data.signedUrl, '_blank', 'noopener,noreferrer');
    } catch (err: any) {
      console.error('Download error:', err);
      setErrorMessage(`Download failed: ${err.message || String(err)}`);
    }
  };

  const handleDelete = async (doc: DocumentItem) => {
    setErrorMessage(null);
    if (doc.isDemo) {
      setDocuments(documents.filter(d => d.id !== doc.id));
      return;
    }

    try {
      // Confirm this authenticated user's metadata record first. RLS scopes this
      // query, avoiding storage deletion for an unverified/stale document.
      const { data: owned, error: ownershipError } = await supabase
        .from('documents')
        .select('id, storage_path')
        .eq('id', doc.id)
        .eq('user_id', user?.id ?? '')
        .maybeSingle();
      if (ownershipError || !owned) throw new Error(ownershipError?.message || 'Document was not found or is no longer accessible');
      if (owned.storage_path) {
        const { error: storageError } = await supabase.storage.from('farmer_documents').remove([owned.storage_path]);
        if (storageError) throw new Error(`Storage deletion failed: ${storageError.message}`);
      }
      const { error } = await supabase.from('documents').delete().eq('id', doc.id).eq('user_id', user?.id ?? '');
      if (error) throw error;

      setDocuments(documents.filter(d => d.id !== doc.id));
      setStatusMessage(`Document "${doc.name}" removed.`);
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      console.error('Delete error:', err);
      setErrorMessage(`Failed to delete document: ${err.message || String(err)}`);
    }
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || doc.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Documents</h1>
            {(!isAuthenticated || isDemoMode) ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Demo Repository
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <Database size={12} className="text-emerald-700" />
                Supabase Storage
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1">
            Store, organize, and view soil test cards, land records, water quality reports, and scheme documents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={uploadCategory}
            onChange={(e) => setUploadCategory(e.target.value as any)}
            className="text-xs bg-white border border-[#E5DDCF] rounded-lg px-3 py-2 font-medium text-[#103D2C] outline-none"
          >
            <option value="Soil Health">Soil Health</option>
            <option value="Land Records">Land Records</option>
            <option value="Lab Reports">Lab Reports</option>
            <option value="Invoices & Schemes">Invoices & Schemes</option>
          </select>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="bg-[#103D2C] hover:bg-[#17643E] text-white px-4 py-2 rounded-lg font-medium text-xs sm:text-sm flex items-center gap-2 transition-colors cursor-pointer disabled:opacity-50"
          >
            {isUploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
            <span>{isUploading ? 'Uploading...' : 'Upload Document'}</span>
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-[#E5DDCF] flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-[#292B26]/40" />
          <input
            type="text"
            placeholder="Search documents by filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg text-xs sm:text-sm focus:outline-none focus:border-[#17643E]"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          <span className="text-xs font-semibold text-[#292B26]/60 flex items-center gap-1">
            <Filter size={12} /> Filter:
          </span>
          {['All', 'Soil Health', 'Land Records', 'Lab Reports', 'Invoices & Schemes'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-all whitespace-nowrap cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-[#103D2C] text-white border-[#103D2C] font-semibold'
                  : 'bg-[#FBF7EF] text-[#292B26]/80 border-[#E5DDCF] hover:border-[#17643E]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Documents Table / List */}
      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-[#103D2C] mx-auto mb-2" />
            <p className="text-xs text-[#292B26]/60">Loading farmer documents from repository...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="py-16 text-center px-4">
            <FileText className="w-12 h-12 text-[#A8C69A] mx-auto mb-3" />
            <h3 className="font-bold text-[#103D2C] mb-1">No Documents Found</h3>
            <p className="text-xs text-[#292B26]/60 max-w-sm mx-auto mb-4">
              {searchTerm || selectedCategory !== 'All'
                ? 'No documents matched your search and filter criteria.'
                : 'No documents uploaded yet. Upload your soil card or 7/12 extract using the button above.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-[#FBF7EF] text-[#103D2C] border-b border-[#E5DDCF] uppercase text-[11px] font-bold tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Document</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Size</th>
                  <th className="py-3.5 px-4">Date</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5DDCF]">
                {filteredDocuments.map((doc) => (
                  <tr key={doc.id} className="hover:bg-[#FBF7EF]/50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-[#103D2C]/10 text-[#103D2C] flex items-center justify-center shrink-0">
                          <FileText size={18} />
                        </div>
                        <div>
                          <p className="font-semibold text-[#292B26] break-all">{doc.name}</p>
                          {doc.isDemo && (
                            <span className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
                              Sample Demo Record
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="bg-[#FBF7EF] text-[#103D2C] border border-[#E5DDCF] px-2.5 py-1 rounded-md text-xs font-medium inline-block">
                        {doc.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#292B26]/70 text-xs">{doc.size}</td>
                    <td className="py-3 px-4 text-[#292B26]/70 text-xs">{doc.uploadDate}</td>
                    <td className="py-3 px-4">
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full inline-block ${
                        doc.status === 'Verified' ? 'bg-emerald-100 text-emerald-800' :
                        doc.status === 'Extracted' ? 'bg-blue-100 text-blue-800' :
                        'bg-amber-100 text-amber-800'
                      }`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleDownload(doc)}
                          title="Download or preview document"
                          className="p-1.5 text-[#103D2C] hover:bg-[#FBF7EF] rounded-md transition-colors cursor-pointer"
                        >
                          <Download size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(doc)}
                          title="Delete document"
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded-md transition-colors cursor-pointer"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
