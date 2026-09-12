export const passwordLength = (value: string): number => Array.from(value).length;
export const validNewPassword = (value: string): boolean => {
  const length = passwordLength(value);
  return length >= 10 && length <= 512;
};
