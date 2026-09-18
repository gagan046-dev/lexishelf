import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { getApiErrorMessage } from "@/api/client";
import { useThemeColors } from "@/theme/ThemeContext";

export function AuthScreen() {
  const colors = useThemeColors();
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isResetOpen, setIsResetOpen] = useState(false);

  const passwordsMismatch = mode === "register" && confirmPassword.length > 0 && password !== confirmPassword;
  const canSubmit =
    email.trim().length > 0 &&
    password.length >= 8 &&
    (mode === "login" || (confirmPassword.length >= 8 && !passwordsMismatch));

  const submit = async () => {
    if (!canSubmit || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      if (mode === "login") await login(email.trim(), password);
      else await register(email.trim(), password);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Authentication failed."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      style={styles.container}
    >
      <View style={styles.brandBlock}>
        <Text style={[styles.brand, { color: colors.text }]}>LexiShelf</Text>
        <Text style={[styles.tagline, { color: colors.muted }]}>Keep the language you discover while reading.</Text>
      </View>

      <View style={[styles.form, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        <View style={[styles.segment, { backgroundColor: colors.surfaceElevated }]}>
          {(["login", "register"] as const).map((option) => {
            const selected = mode === option;
            return (
              <Pressable
                key={option}
                onPress={() => {
                  setMode(option);
                  setError(null);
                  setConfirmPassword("");
                }}
                style={[styles.segmentOption, selected && { backgroundColor: colors.primary }]}
              >
                <Text style={{ color: selected ? colors.onPrimary : colors.muted, fontWeight: "700" }}>
                  {option === "login" ? "Sign in" : "Create account"}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <TextInput
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
          placeholder="Email"
          placeholderTextColor={colors.muted}
          style={[styles.input, { color: colors.text, borderColor: colors.border }]}
        />
        <TextInput
          autoCapitalize="none"
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          secureTextEntry
          value={password}
          onChangeText={setPassword}
          onSubmitEditing={() => void submit()}
          placeholder="Password"
          placeholderTextColor={colors.muted}
          style={[styles.input, { color: colors.text, borderColor: colors.border }]}
        />
        {mode === "register" ? (
          <TextInput
            autoCapitalize="none"
            autoComplete="new-password"
            secureTextEntry
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            onSubmitEditing={() => void submit()}
            placeholder="Confirm password"
            placeholderTextColor={colors.muted}
            style={[styles.input, { color: colors.text, borderColor: passwordsMismatch ? colors.danger : colors.border }]}
          />
        ) : null}
        {passwordsMismatch ? (
          <Text style={[styles.error, { color: colors.danger }]}>Passwords do not match.</Text>
        ) : null}
        {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}

        {mode === "login" ? (
          <Pressable onPress={() => setIsResetOpen(true)} style={styles.forgotLink} hitSlop={8}>
            <Text style={{ color: colors.primary, fontSize: 13, fontWeight: "600" }}>Forgot password?</Text>
          </Pressable>
        ) : null}

        <Pressable
          disabled={!canSubmit || isSubmitting}
          onPress={() => void submit()}
          style={({ pressed }) => [
            styles.submit,
            { backgroundColor: colors.primary, opacity: !canSubmit || isSubmitting ? 0.45 : pressed ? 0.75 : 1 },
          ]}
        >
          {isSubmitting ? (
            <ActivityIndicator color={colors.onPrimary} />
          ) : (
            <Text style={[styles.submitText, { color: colors.onPrimary }]}>
              {mode === "login" ? "Sign in" : "Create account"}
            </Text>
          )}
        </Pressable>
      </View>

      <ResetPasswordModal visible={isResetOpen} onClose={() => setIsResetOpen(false)} />
    </KeyboardAvoidingView>
  );
}

function ResetPasswordModal({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const colors = useThemeColors();
  const { forgotPassword, resetPassword } = useAuth();
  const [step, setStep] = useState<"request" | "reset">("request");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setStep("request");
    setEmail("");
    setCode("");
    setNewPassword("");
    setConfirmNewPassword("");
    setMessage(null);
    setError(null);
  };

  const requestCode = async () => {
    if (!email.trim() || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const result = await forgotPassword(email.trim());
      if (result.devResetToken) {
        setCode(result.devResetToken);
        setStep("reset");
        setMessage("Email delivery isn't configured yet, so your reset code was auto-filled below (development only).");
      } else {
        setMessage(result.message);
        setStep("reset");
      }
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not request a reset code."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitReset = async () => {
    if (!code.trim() || newPassword.length < 8 || newPassword !== confirmNewPassword || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await resetPassword(code.trim(), newPassword);
      reset();
      onClose();
    } catch (resetError) {
      setError(getApiErrorMessage(resetError, "Could not reset your password."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const mismatch = confirmNewPassword.length > 0 && newPassword !== confirmNewPassword;

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.modalBackdrop}
      >
        <View style={[styles.modal, { backgroundColor: colors.background, borderColor: colors.border }]}>
          <Text style={[styles.modalTitle, { color: colors.text }]}>Reset your password</Text>

          {step === "request" ? (
            <>
              <Text style={[styles.modalSubtitle, { color: colors.muted }]}>
                Enter your account email and we'll send a reset code.
              </Text>
              <TextInput
                autoCapitalize="none"
                autoComplete="email"
                keyboardType="email-address"
                value={email}
                onChangeText={setEmail}
                placeholder="Email"
                placeholderTextColor={colors.muted}
                style={[styles.input, { color: colors.text, borderColor: colors.border, marginTop: 16 }]}
              />
              {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}
              <Pressable
                disabled={!email.trim() || isSubmitting}
                onPress={() => void requestCode()}
                style={({ pressed }) => [
                  styles.submit,
                  { backgroundColor: colors.primary, opacity: !email.trim() || isSubmitting ? 0.45 : pressed ? 0.75 : 1 },
                ]}
              >
                {isSubmitting ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={[styles.submitText, { color: colors.onPrimary }]}>Send reset code</Text>}
              </Pressable>
            </>
          ) : (
            <>
              {message ? <Text style={[styles.modalSubtitle, { color: colors.muted }]}>{message}</Text> : null}
              <TextInput
                autoCapitalize="none"
                value={code}
                onChangeText={setCode}
                placeholder="Reset code"
                placeholderTextColor={colors.muted}
                style={[styles.input, { color: colors.text, borderColor: colors.border, marginTop: 16 }]}
              />
              <TextInput
                autoCapitalize="none"
                secureTextEntry
                value={newPassword}
                onChangeText={setNewPassword}
                placeholder="New password"
                placeholderTextColor={colors.muted}
                style={[styles.input, { color: colors.text, borderColor: colors.border }]}
              />
              <TextInput
                autoCapitalize="none"
                secureTextEntry
                value={confirmNewPassword}
                onChangeText={setConfirmNewPassword}
                placeholder="Confirm new password"
                placeholderTextColor={colors.muted}
                style={[styles.input, { color: colors.text, borderColor: mismatch ? colors.danger : colors.border }]}
              />
              {mismatch ? <Text style={[styles.error, { color: colors.danger }]}>Passwords do not match.</Text> : null}
              {error ? <Text style={[styles.error, { color: colors.danger }]}>{error}</Text> : null}
              <Pressable
                disabled={!code.trim() || newPassword.length < 8 || mismatch || isSubmitting}
                onPress={() => void submitReset()}
                style={({ pressed }) => [
                  styles.submit,
                  {
                    backgroundColor: colors.primary,
                    opacity: !code.trim() || newPassword.length < 8 || mismatch || isSubmitting ? 0.45 : pressed ? 0.75 : 1,
                  },
                ]}
              >
                {isSubmitting ? <ActivityIndicator color={colors.onPrimary} /> : <Text style={[styles.submitText, { color: colors.onPrimary }]}>Reset password</Text>}
              </Pressable>
            </>
          )}

          <Pressable
            onPress={() => {
              reset();
              onClose();
            }}
            style={styles.cancelLink}
          >
            <Text style={{ color: colors.muted, fontSize: 13, fontWeight: "600" }}>Cancel</Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24 },
  brandBlock: { marginBottom: 28 },
  brand: { fontSize: 36, fontWeight: "800" },
  tagline: { fontSize: 15, lineHeight: 21, marginTop: 6, maxWidth: 320 },
  form: { borderRadius: 8, borderWidth: 1, padding: 18 },
  segment: { flexDirection: "row", borderRadius: 8, padding: 4, marginBottom: 18 },
  segmentOption: { flex: 1, minHeight: 38, alignItems: "center", justifyContent: "center", borderRadius: 6 },
  input: { minHeight: 50, borderBottomWidth: 1, fontSize: 15, marginBottom: 12 },
  error: { fontSize: 13, lineHeight: 18, marginBottom: 10 },
  forgotLink: { alignSelf: "flex-end", marginBottom: 14, marginTop: -4 },
  submit: { minHeight: 48, borderRadius: 8, alignItems: "center", justifyContent: "center", marginTop: 6 },
  submitText: { fontSize: 15, fontWeight: "700" },
  modalBackdrop: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "rgba(0,0,0,0.5)" },
  modal: { borderRadius: 8, borderWidth: 1, padding: 20 },
  modalTitle: { fontSize: 20, fontWeight: "800", marginBottom: 6 },
  modalSubtitle: { fontSize: 13, lineHeight: 19 },
  cancelLink: { alignSelf: "center", marginTop: 14 },
});