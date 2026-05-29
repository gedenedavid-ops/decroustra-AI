import React, { useState, useRef, useEffect, useCallback } from "react";
import { Plus, ChevronDown, ArrowUp, X, FileText, Loader2, Check, Archive } from "lucide-react";

/* --- ICONS --- */
export const Icons = {
    Logo: (props: React.SVGProps<SVGSVGElement>) => (
        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" role="presentation" {...props}>
            <defs>
                <ellipse id="petal-pair" cx="100" cy="100" rx="90" ry="22" />
            </defs>
            <g fill="#D46B4F" fillRule="evenodd">
                <use href="#petal-pair" transform="rotate(0 100 100)" />
                <use href="#petal-pair" transform="rotate(45 100 100)" />
                <use href="#petal-pair" transform="rotate(90 100 100)" />
                <use href="#petal-pair" transform="rotate(135 100 100)" />
            </g>
        </svg>
    ),
    Plus: Plus,
    Thinking: (props: React.SVGProps<SVGSVGElement>) => <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg" {...props}><path d="M10.3857 2.50977C14.3486 2.71054 17.5 5.98724 17.5 10C17.5 14.1421 14.1421 17.5 10 17.5C5.85786 17.5 2.5 14.1421 2.5 10C2.5 9.72386 2.72386 9.5 3 9.5C3.27614 9.5 3.5 9.72386 3.5 10C3.5 13.5899 6.41015 16.5 10 16.5C13.5899 16.5 16.5 13.5899 16.5 10C16.5 6.5225 13.7691 3.68312 10.335 3.50879L10 3.5L9.89941 3.49023C9.67145 3.44371 9.5 3.24171 9.5 3C9.5 2.72386 9.72386 2.5 10 2.5L10.3857 2.50977ZM10 5.5C10.2761 5.5 10.5 5.72386 10.5 6V9.69043L13.2236 11.0527C13.4706 11.1762 13.5708 11.4766 13.4473 11.7236C13.3392 11.9397 13.0957 12.0435 12.8711 11.9834L12.7764 11.9473L9.77637 10.4473C9.60698 10.3626 9.5 10.1894 9.5 10V6C9.5 5.72386 9.72386 5.5 10 5.5ZM3.66211 6.94141C4.0273 6.94159 4.32303 7.23735 4.32324 7.60254C4.32324 7.96791 4.02743 8.26446 3.66211 8.26465C3.29663 8.26465 3 7.96802 3 7.60254C3.00021 7.23723 3.29676 6.94141 3.66211 6.94141ZM4.95605 4.29395C5.32146 4.29404 5.61719 4.59063 5.61719 4.95605C5.6171 5.3214 5.3214 5.61709 4.95605 5.61719C4.59063 5.61719 4.29403 5.32146 4.29395 4.95605C4.29395 4.59057 4.59057 4.29395 4.95605 4.29395ZM7.60254 3C7.96802 3 8.26465 3.29663 8.26465 3.66211C8.26446 4.02743 7.96791 4.32324 7.60254 4.32324C7.23736 4.32302 6.94159 4.0273 6.94141 3.66211C6.94141 3.29676 7.23724 3.00022 7.60254 3Z"></path></svg>,
    SelectArrow: ChevronDown,
    ArrowUp: ArrowUp,
    X: X,
    FileText: FileText,
    Loader2: Loader2,
    Check: Check,
    Archive: Archive,
};

/* --- UTILS --- */
const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

interface AttachedFile {
    id: string;
    file: File;
    type: string;
    preview: string | null;
    uploadStatus: string;
}

const FilePreviewCard: React.FC<{ file: AttachedFile; onRemove: (id: string) => void }> = ({ file, onRemove }) => {
    const isImage = file.type.startsWith("image/") && file.preview;
    return (
        <div className="relative group flex-shrink-0 w-24 h-24 rounded-xl overflow-hidden border border-bg-300 bg-bg-200 transition-all hover:border-text-400">
            {isImage ? (
                <img src={file.preview!} alt={file.file.name} className="w-full h-full object-cover" />
            ) : (
                <div className="w-full h-full p-3 flex flex-col justify-between">
                    <Icons.FileText className="w-4 h-4 text-text-300" />
                    <p className="text-xs truncate">{file.file.name}</p>
                </div>
            )}
            <button onClick={() => onRemove(file.id)} className="absolute top-1 right-1 p-1 bg-black/50 rounded-full text-white opacity-0 group-hover:opacity-100"><Icons.X className="w-3 h-3" /></button>
        </div>
    );
};

export const ClaudeChatInput: React.FC<{ onSendMessage: (data: any) => void }> = ({ onSendMessage }) => {
    const [message, setMessage] = useState("");
    const [files, setFiles] = useState<AttachedFile[]>([]);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSend = () => {
        if (!message.trim() && files.length === 0) return;
        onSendMessage({ message, files });
        setMessage("");
        setFiles([]);
    };

    return (
        <div className="relative w-full max-w-2xl mx-auto p-4 border border-bg-300 rounded-2xl bg-white shadow-sm">
            <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="How can I help you today?"
                className="w-full bg-transparent border-none outline-none resize-none"
            />
            <div className="flex justify-between items-center mt-2">
                <button onClick={() => {}} className="p-2 text-text-400 hover:text-text-200"><Icons.Plus /></button>
                <button onClick={handleSend} className="p-2 bg-accent text-white rounded-xl"><Icons.ArrowUp /></button>
            </div>
        </div>
    );
};
