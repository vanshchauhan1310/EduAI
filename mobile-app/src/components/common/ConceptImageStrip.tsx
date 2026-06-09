import React from 'react';
import { View, Text, Image, ScrollView, TouchableOpacity, StyleSheet, Linking } from 'react-native';
import { ConceptImage } from '../../types';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

interface ConceptImageStripProps {
  images?: (ConceptImage & { _description?: string })[];
}

const CARD_WIDTH = 140;
const CARD_HEIGHT = 100;

// Tapping a card opens the Wikimedia Commons file page — gives full
// attribution/license context without needing a custom image-viewer modal.
export default function ConceptImageStrip({ images }: ConceptImageStripProps) {
  if (!images || images.length === 0) return null;

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      style={styles.strip}
      contentContainerStyle={styles.content}
    >
      {images.map((image, index) => {
        // Real image from Wikimedia Commons
        if (image.thumbnail_url) {
          return (
            <TouchableOpacity
              key={`${image.source_url}-${index}`}
              style={styles.card}
              activeOpacity={0.85}
              onPress={() => image.source_url && Linking.openURL(image.source_url)}
            >
              <Image source={{ uri: image.thumbnail_url }} style={styles.image} resizeMode="cover" />
              <Text style={styles.caption} numberOfLines={1}>{image.attribution || image.title}</Text>
            </TouchableOpacity>
          );
        }
        // Gemini-generated diagram description (no real image available)
        if (image._description) {
          return (
            <View key={`desc-${index}`} style={styles.descCard}>
              <Text style={styles.descTitle}>{image.title}</Text>
              <Text style={styles.descText} numberOfLines={6}>{image._description}</Text>
              <Text style={styles.caption}>{image.attribution}</Text>
            </View>
          );
        }
        return null;
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  strip: {
    marginVertical: Spacing.sm,
  },
  content: {
    gap: Spacing.sm,
    paddingHorizontal: 2,
  },
  card: {
    width: CARD_WIDTH,
  },
  image: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    borderRadius: BorderRadius.md,
    backgroundColor: Colors.neutral[100],
  },
  caption: {
    marginTop: 4,
    fontSize: Typography.sizes.xs,
    color: Colors.neutral[500],
  },
  descCard: {
    width: 220,
    padding: Spacing.sm,
    backgroundColor: Colors.primary[50],
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.neutral[200],
  },
  descTitle: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.bold,
    color: Colors.primary[700],
    marginBottom: 4,
  },
  descText: {
    fontSize: Typography.sizes.xs,
    color: Colors.neutral[700],
    lineHeight: 16,
  },
});