/**
 * Формы данных API.
 *
 * @typedef {{clicks: number, unique: number, bots: number}} Stats
 * @typedef {{id: number, name: string, state: string|null, alias?: string|null,
 *   tracking_url?: string|null}} Campaign
 * @typedef {{id: number, name: string, state: string|null}} Offer
 * @typedef {{offer_id: number, name: string, share: number, state: string|null}} StreamOffer
 * @typedef {{name: string, mode: string, values: string[]}} StreamFilter
 * @typedef {{id: number, name: string, position: number, enabled: boolean,
 *   kind: "redirect"|"offers", target: string|null, filters: StreamFilter[],
 *   offers: StreamOffer[], stats: Stats}} Stream
 * @typedef {{campaign: Campaign, streams: Stream[], totals: Stats, stats_error?: string|null, range: string}} CampaignDetails
 * @typedef {{prefix: string, domain: string, group: string, source: string,
 *   redirect_url: string}} Meta
 */
export {};
