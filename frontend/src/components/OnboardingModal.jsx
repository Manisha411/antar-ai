import { createPortal } from 'react-dom'

const ONBOARDING_KEY = 'journal-onboarding-done'

export function hasSeenOnboarding() {
  try {
    return localStorage.getItem(ONBOARDING_KEY) === 'true'
  } catch {
    return false
  }
}

export function setOnboardingDone() {
  try {
    localStorage.setItem(ONBOARDING_KEY, 'true')
  } catch {}
}

export default function OnboardingModal({ onDismiss }) {
  const modal = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true" aria-labelledby="onboarding-title">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
        <h2 id="onboarding-title" className="text-lg font-semibold text-slate-800">What to expect</h2>
        <p className="text-slate-600 text-sm">
          Each day you'll get a short prompt. Write a few sentences (or more) about how you're feeling or what's on your mind. Your entries are private.
        </p>
        <p className="text-slate-600 text-sm font-medium">Example prompts:</p>
        <ul className="text-slate-600 text-sm list-disc list-inside space-y-1">
          <li>What's one thing you're grateful for right now?</li>
          <li>What was today's win?</li>
          <li>One worry to let go of.</li>
        </ul>
        <p className="text-slate-600 text-sm">
          Just write a sentence or two. There's no right or wrong.
        </p>
        <button
          type="button"
          onClick={onDismiss}
          className="w-full bg-slate-800 text-white rounded-lg py-2 font-medium hover:bg-slate-700"
        >
          Got it
        </button>
      </div>
    </div>
  )
  return typeof document !== 'undefined' ? createPortal(modal, document.body) : modal
}
