import React, { useRef, useState, useEffect } from "react";
import { X } from "lucide-react";
import * as htmlToImage from "html-to-image";
import jsPDF from "jspdf";
import QRCode from "qrcode";

const TransactionReceiptModal = ({ transaction, onClose }) => {
  const receiptRef = useRef(null);
  const [qrUrl, setQrUrl] = useState("");

  console.log('Receipt - Full transaction data:', transaction);

  // Helper to safely get values
  const getValue = (value, fallback = 'N/A') => value || fallback;

  // Determine if user is sender or recipient
  const isDebit = transaction.is_debit;

  // Map the transaction data to receipt fields
  const receiptData = {
    // Amount
    amount: transaction.amount || '0.00',
    
    // Status
    status: transaction.status_display || transaction.status || 'COMPLETED',
    
    // Date/Time - format the created_at timestamp
    date: transaction.created_at 
      ? new Date(transaction.created_at).toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })
      : 'N/A',
    
    // Sender (the person who sent the money)
    sender_name: isDebit
      ? getValue(transaction.user_name, 'You')  // Current user is sender
      : getValue(transaction.counterparty_name, transaction.user_name),  // Other party is sender
    
    sender_account: isDebit
      ? getValue(transaction.user_account)
      : getValue(transaction.counterparty_account, transaction.user_account),
    
    // Bank (always Pemon for both)
    sender_bank: 'Pemon',
    
    // Recipient (the person receiving the money)
    recipient_name: isDebit
      ? getValue(transaction.counterparty_name, transaction.recipient_name)  // Other party is recipient
      : getValue(transaction.user_name, 'You'),  // Current user is recipient
    
    recipient_account: isDebit
      ? getValue(transaction.counterparty_account, transaction.recipient_account)
      : getValue(transaction.user_account),
    
    // Transaction reference
    reference: getValue(transaction.reference),
  };

  console.log('Receipt data mapped:', receiptData);

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return d.toLocaleString();
  };

  const maskAccount = (acc) => {
    if (!acc || acc === 'N/A' || acc.length < 6) return acc || "N/A";
    return `${acc.slice(0, 4)}****${acc.slice(-2)}`;
  };

  const handleShare = async (type) => {
    if (!receiptRef.current) return;

    const dataUrl = await htmlToImage.toPng(receiptRef.current);

    if (type === "png") {
      const link = document.createElement("a");
      link.download = `receipt-${receiptData.reference}.png`;
      link.href = dataUrl;
      link.click();
    }

    if (type === "pdf") {
      const pdf = new jsPDF();
      const imgProps = pdf.getImageProperties(dataUrl);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

      pdf.addImage(dataUrl, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save(`receipt-${receiptData.reference}.pdf`);
    }
  };

  useEffect(() => {
    const generateQR = async () => {
      const qr = await QRCode.toDataURL(
        JSON.stringify({
          id: transaction.id,
          ref: receiptData.reference,
          amount: receiptData.amount,
        })
      );
      setQrUrl(qr);
    };
    generateQR();
  }, [transaction, receiptData]);

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">

      {/* RECEIPT CARD */}
      <div
        ref={receiptRef}
        className="bg-white w-[360px] rounded-2xl shadow-xl p-5"
      >

        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-lg font-semibold text-center text-blue-600">
            Pemon
          </h1>
          <button onClick={onClose}>
            <X size={18} className="hover:cursor-pointer" />
          </button>
        </div>

        {/* Title */}
        <div className="text-center mb-3">
           <span className="text-sm font-semibold text-gray-800">
            Transaction Receipt
          </span>
          <p className="text-2xl font-bold text-gray-900">
            ₦{receiptData.amount}
          </p>
          <p className="text-sm text-green-600 font-medium">
            {receiptData.status}
          </p>
        </div>

        <hr className="border-dashed my-3" />

        {/* Details */}
        <div className="space-y-2 text-sm">

          <Row
            label="Date/Time"
            value={receiptData.date}
          />

          <Row
            label="Sender"
            value={receiptData.sender_name}
          />

        

          <Row
            label="Bank Name"
            value={receiptData.sender_bank}
          />

          <Row
            label="Recipient"
            value={receiptData.recipient_name}
          />

          

          <Row
            label="Transaction No"
            value={receiptData.reference}
          />

        </div>

        <hr className="border-dashed my-3" />

        {/* QR */}
        {qrUrl && (
          <div className="flex flex-col items-center">
            <img src={qrUrl} alt="QR" className="w-20 h-20" />
            <p className="text-[10px] text-gray-400 mt-1">
              Scan to verify transaction
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-4 text-xs text-gray-400">
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => handleShare("png")}
              className="flex-1 py-2 bg-blue-900 text-white text-sm font-medium rounded-lg hover:bg-black hover:cursor-pointer transition"
            >
              Share as Image
            </button>

            <button
              onClick={() => handleShare("pdf")}
              className="flex-1 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 hover:cursor-pointer transition"
            >
              Share as PDF
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const Row = ({ label, value }) => (
  <div className="flex justify-between gap-4">
    <span className="text-gray-500">{label}</span>
    <span className="text-right font-medium break-all">
      {value || "N/A"}
    </span>
  </div>
);

export default TransactionReceiptModal;